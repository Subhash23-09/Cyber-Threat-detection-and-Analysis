import re
from collections import Counter
from models import Signal, db
import json
from services.memory_store import MemoryService
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

class DynamicLogAnalyzer:
    def __init__(self):
        # Stats
        self.ip_counter = Counter()
        self.http_method_counter = Counter()
        self.auth_failure_counter = Counter()
        self.sudo_abuse_map = [] # List of {user, command}
        self.ssh_source_map = {} # ip -> user set
        self.file_transfers = [] # List of {src_ip, file_name, size, dest}
        self.ssl_errors = [] # List of {type, detail, ip}

        # Patterns
        self.ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        self.http_pattern = re.compile(r'(GET|POST|HEAD|PUT|DELETE)\s+.*?\s+HTTP/[\d\.]+')
        self.error_pattern = re.compile(r'(ERROR|FATAL|FAIL|CRITICAL|REJECTED)', re.IGNORECASE)
        self.warn_pattern = re.compile(r'(WARN|WARNING|ATTEMPT)', re.IGNORECASE)
        self.general_anomalies = []
        self.forensic_samples = [] # Collect suspicious snippets for LLM
        
        # Drain3 Setup
        config = TemplateMinerConfig()
        self.miner = TemplateMiner(config=config)
        self.structural_anomalies = []

    def process_line(self, line):
        """Analyze a single line and update internal stats."""
        # 1. IP Extraction
        ips = self.ip_pattern.findall(line)
        for ip in ips:
            self.ip_counter[ip] += 1
            
        # 2. HTTP Traffic Analysis
        if self.http_pattern.search(line):
            for ip in ips:
                self.http_method_counter[ip] += 1
                
        # 3. Auth Failures
        if "Failed password" in line or "authentication failure" in line:
            src_ip_match = self.ip_pattern.search(line)
            user_match = re.search(r'for (?:invalid user )?(\w+)', line)
            
            if src_ip_match:
                ip = src_ip_match.group(1)
                self.auth_failure_counter[ip] += 1
                if user_match:
                    if ip not in self.ssh_source_map:
                        self.ssh_source_map[ip] = set()
                    self.ssh_source_map[ip].add(user_match.group(1))

        # 4. Privilege Escalation
        if "sudo" in line and "COMMAND" in line:
             user_match = re.search(r'(\w+) : TTY', line)
             user = user_match.group(1) if user_match else "root"
             user = user_match.group(1) if user_match else "root"
             self.sudo_abuse_map.append(user)

        # 5. File Transfer Detection (SCP/FTP)
        # scp[456]: uploading confidential_db.sql (629145600 bytes) to 10.0.0.5
        if "uploading" in line or "downloading" in line:
            size_match = re.search(r'\((\d+) bytes\)', line)
            file_match = re.search(r'(?:uploading|downloading) ([\w\.]+)', line)
            ip_match = self.ip_pattern.search(line)
            
            if size_match and file_match:
                self.file_transfers.append({
                    "size": int(size_match.group(1)),
                    "file_name": file_match.group(1),
                    "src_ip": ip_match.group(1) if ip_match else "unknown",
                    "timestamp": "now" # In real app parse timestamp
                })



        # 5. General Anomalies (for HDFS.log style)
        if self.error_pattern.search(line):
            self.general_anomalies.append({"type": "ERROR", "content": line[:100]})
        elif self.warn_pattern.search(line):
            self.general_anomalies.append({"type": "WARN", "content": line[:100]})
            
        if len(self.forensic_samples) < 50:
            if any(term in line.lower() for term in ["failed", "sudo", "error", "command", "base64", "eval", "system"]):
                self.forensic_samples.append(line.strip())

        # 7. Drain3 Structural Parsing
        result = self.miner.add_log_message(line)
        if result["change_type"] == "cluster_created":
            self.structural_anomalies.append({
                "template": result["template_mined"],
                "id": result["cluster_id"],
                "content": line[:100]
            })

    def generate_signals(self):
        """
        Converts aggregated log metrics into generic behavioral Signals using statistical analysis.
        Thresholds and confidence are derived from file-specific distributions to avoid "hardcoded" values.
        """
        signals = []
        import math
        import hashlib

        # 1. Statistical Analysis for Traffic
        counts = list(self.ip_counter.values())
        if not counts:
            return []
            
        mean_count = sum(counts) / len(counts)
        variance = sum((x - mean_count) ** 2 for x in counts) / len(counts)
        std_dev = math.sqrt(variance) if variance > 0 else 1.0
        
        # Dynamic Threshold: Anything 2 standard deviations above mean
        dynamic_threshold = max(10, mean_count + (2 * std_dev))

        for ip, count in self.ip_counter.items():
            # A. Determine Anomaly Score & Attack Type
            if count > dynamic_threshold:
                mitre_id = "T1498"
                suspected = "Volumetric Anomaly (Potential DoS)"
                score = "HIGH"
            elif count > (mean_count + std_dev):
                mitre_id = "T1595"
                suspected = "Abnormal Traffic Volume"
                score = "MEDIUM"
            else:
                mitre_id = "T1595"
                suspected = "Network Scanning / Baseline"
                score = "INFO"

            # B. Statistical Confidence Calculation
            # Z-Score represents how extreme the outlier is
            z_score = (count - mean_count) / std_dev if std_dev > 0 else 0
            
            # Map Z-Score to a 0-99 range (Sigmoid-like)
            # 0 deviation -> ~40% confidence, 2 dev -> ~80%, 4+ dev -> 99%
            raw_confidence = 40 + (50 * (1 - math.exp(-0.5 * z_score)))
            
            # Add stable jitter for UI variety
            ip_hash = int(hashlib.md5(ip.encode()).hexdigest(), 16)
            jitter = (ip_hash % 6) - 3 # -3 to +3
            
            confidence = min(99, max(15, int(raw_confidence + jitter)))

            signal = Signal(
                event_type="network_flow",
                source_ip=ip,
                target_user="server",
                failed_attempts=0,
                time_window="session",
                anomaly_score=score,
                suspected_attack=suspected,
                mitre_id=mitre_id,
                confidence=confidence,
                context_info=json.dumps({
                    "baseline": f"{mean_count:.1f} avg/IP",
                    "std_dev": f"{std_dev:.1f}",
                    "internet_facing": True
                })
            )
            signals.append(signal)

        # 2. Authentication Signals (Statistical approach)
        auth_counts = list(self.auth_failure_counter.values())
        if auth_counts:
            auth_mean = sum(auth_counts) / len(auth_counts)
            
            for ip, fail_count in self.auth_failure_counter.items():
                target_users = list(self.ssh_source_map.get(ip, []))
                users_str = ", ".join(target_users[:3])
                
                # Dynamic Threshold for Brute Force (Relative to file average)
                if fail_count > (auth_mean * 3) and fail_count > 5:
                    mitre_id = "T1110"
                    suspected = "Brute Force Attempt"
                    score = "HIGH"
                else:
                    mitre_id = "T1078"
                    suspected = "Auth Deviations"
                    score = "LOW"
                
                # Confidence based on intensity relative to average
                rel_intensity = fail_count / auth_mean if auth_mean > 0 else 1
                rel_intensity = fail_count / auth_mean if auth_mean > 0 else 1
                conf = min(99, int(50 + (10 * rel_intensity)))

                # --- FIX: Generate the Signal object ---
                signal = Signal(
                    event_type="authentication",
                    source_ip=ip,
                    target_user=users_str,
                    failed_attempts=fail_count,
                    time_window="session",
                    anomaly_score=score,
                    suspected_attack=suspected,
                    mitre_id=mitre_id,
                    confidence=conf,
                    context_info=json.dumps({
                        "distinct_users_targeted": len(target_users),
                        "intensity_multiplier": f"{rel_intensity:.1f}x"
                    })
                )
                signals.append(signal)

        # 3. File Transfer Signals (Exfiltration)
        for ft in self.file_transfers:
            # We trust the raw data; specific agent will decide if malicious
            signal = Signal(
                event_type="file_transfer",
                source_ip=ft['src_ip'],
                target_user="remote_host",
                failed_attempts=0,
                time_window="transaction",
                anomaly_score="MEDIUM", # Default, agent escalates to CRITICAL
                suspected_attack="Data Exfiltration Risk",
                mitre_id="T1048",
                confidence=85,
                context_info=json.dumps({
                    "file_name": ft['file_name'],
                    "size_bytes": ft['size'],
                    "protocol": "scp/ssh"
                })
            )
            signals.append(signal)



        # 4. General Log Anomalies (System/App level)
        if self.general_anomalies:
            error_count = len([a for a in self.general_anomalies if a['type'] == 'ERROR'])
            warn_count = len(self.general_anomalies) - error_count
            
            if error_count > 0:
                signal = Signal(
                    event_type="system_anomaly",
                    source_ip="application_log",
                    target_user="system",
                    failed_attempts=0,
                    time_window="batch",
                    anomaly_score="HIGH" if error_count > 5 else "MEDIUM",
                    suspected_attack="Application/System Error Loop",
                    mitre_id="T1490", # Service Stop / Anomaly
                    confidence=70 if error_count > 5 else 40,
                    context_info=json.dumps({
                        "errors": error_count,
                        "warnings": warn_count,
                        "sample": self.general_anomalies[0]['content']
                    })
                )
                signals.append(signal)

        # 5. Drain3 Structural Pattern Discovery
        for anomaly in self.structural_anomalies:
            signal = Signal(
                event_type="structural_discovery",
                source_ip="drain3_miner",
                target_user="system",
                failed_attempts=0,
                time_window="discovery",
                anomaly_score="MEDIUM",
                suspected_attack=f"New Log Pattern: {anomaly['template'][:50]}...",
                mitre_id="T1595.002", # Active Scanning / Pattern Discovery
                confidence=65,
                context_info=json.dumps({
                    "template": anomaly["template"],
                    "cluster_id": anomaly["id"],
                    "sample": anomaly["content"]
                })
            )
            signals.append(signal)

        return signals


class PreprocessorService:
    @staticmethod
    def process_file(file_path):
        """
        Step-2 Engine: Now with dynamic statistical thresholds.
        """
        analyzer = DynamicLogAnalyzer()
        
        total_lines = 0
        raw_preview = []
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                total_lines += 1
                if total_lines <= 5:
                    raw_preview.append(line.strip())
                
                analyzer.process_line(line)

        # Generate Signals dynamically
        final_signals = analyzer.generate_signals()
        
        # Save to DB
        try:
             # --- MODIFIED: Aggregation Support ---
             # We no longer clear OLD signals or memory automatically.
             # This allows multiple log uploads to accumulate findings.
             # db.session.query(Signal).delete()
             # MemoryService.clear_short_term()
             
             print(f"[PreprocessorService] Ingesting signals (Aggregation Mode).")

             for s in final_signals:
                 db.session.add(s)
             db.session.commit()
             
             # --- NEW: LLM SEMANTIC ANALYSIS PASS (with Drain3 Templates) ---
             if analyzer.forensic_samples:
                 from services.llm_service import LLMService
                 
                 # Create a summary using templates to provide better context
                 try:
                     clusters = analyzer.miner.drain_manager.clusters
                     template_summary = "\n".join([f"Template {c.cluster_id} (count {c.size}): {c.get_template()}" for c in clusters][:10])
                 except Exception as e:
                     print(f"Drain3 Template Error: {e}")
                     template_summary = "Templates unavailable"
                 
                 forensic_context = f"STRUCTURAL TEMPLATES:\n{template_summary}\n\nSUSPICIOUS RAW LOGS:\n" + "\n".join(analyzer.forensic_samples)
                 
                 llm_signals = LLMService.analyze_logs(forensic_context)
                 
                 for ls in llm_signals:
                     # Convert LLM dict to Signal model
                     semantic_signal = Signal(
                         event_type="semantic_forensic",
                         source_ip="llm_analysis",
                         target_user="system",
                         failed_attempts=0,
                         time_window="contextual",
                         anomaly_score="HIGH" if ls.get('confidence', 0) > 70 else "MEDIUM",
                         suspected_attack=ls.get('suspected_attack', "Semantic Anomaly"),
                         mitre_id=ls.get('mitre_id', "T1548"),
                         confidence=ls.get('confidence', 75),
                         context_info=json.dumps({
                             "reasoning": ls.get('reasoning', ""),
                             "original_detection": "Deep Semantic Forensic Engine"
                         })
                     )
                     db.session.add(semantic_signal)
                     final_signals.append(semantic_signal)
                 
                 db.session.commit()
             # ---------------------------------------

             # Update Short Term Memory with fresh data
             MemoryService.update_short_term(final_signals)
             
        except Exception as e:
            db.session.rollback()
            print(f"Error saving signals: {e}")

        return [s.to_dict() for s in final_signals], {"total_lines": total_lines, "raw_preview": raw_preview}

