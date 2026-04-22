import re
import math
import hashlib
import json
import aiohttp
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models_v2 import SecuritySignal, IncidentMemory, Asset
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from config import Config
from services_v2.anomaly_service import AnomalyService
class FieldNormalizer:
    """
    Normalizes log fields from different sources (Windows, SSH, Firewall)
    into a unified schema for consistent processing.
    """
    
    FIELD_MAPPINGS = {
        'windows': {
            'source_ip': ['IpAddress', 'SourceAddress', 'ClientAddress'],
            'target_user': ['TargetUserName', 'UserName', 'Account'],
            'timestamp': ['TimeCreated', 'EventTime', 'LogTime'],
            'event_type': ['EventID', 'EventType'],
            'action': ['Action', 'Activity']
        },
        'ssh': {
            'source_ip': ['src_ip', 'remote_ip', 'from'],
            'target_user': ['user', 'username', 'target'],
            'timestamp': ['timestamp', 'time', 'datetime'],
            'event_type': ['event', 'type', 'message_type'],
            'action': ['action', 'result', 'status']
        },
        'firewall': {
            'source_ip': ['source_ip', 'src', 'origin_ip'],
            'target_user': ['dst_user', 'dest_user', 'target_user'],
            'timestamp': ['log_time', 'time', 'timestamp'],
            'event_type': ['action', 'event_type', 'rule'],
            'action': ['action', 'verdict', 'result']
        }
    }
    
    @staticmethod
    def normalize_log_entry(raw_line: str, source_type: str = 'ssh') -> dict:
        """
        Extract and normalize fields from a raw log line.
        """
        normalized = {
            'source_ip': None,
            'target_user': None,
            'timestamp': datetime.utcnow(),
            'event_type': 'unknown',
            'action': 'unknown',
            'raw_message': raw_line
        }
        
        # Extract IP addresses (Strict validation 0-255)
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        ips = ip_pattern.findall(raw_line)
        
        valid_ip = None
        for ip in ips:
            # Validate octets are 0-255
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                valid_ip = ip
                break
                
        if valid_ip:
            normalized['source_ip'] = valid_ip
        
        # Extract usernames
        user_patterns = [
            r'for (?:invalid user )?(\w+)',
            r'user[=:]?\s*(\w+)',
            r'TargetUserName[=:]?\s*(\w+)'
        ]
        for pattern in user_patterns:
            match = re.search(pattern, raw_line, re.IGNORECASE)
            if match:
                normalized['target_user'] = match.group(1)
                break
        
        # Detect event type
        if 'Failed password' in raw_line or 'authentication failure' in raw_line:
            normalized['event_type'] = 'auth_failure'
            normalized['action'] = 'failed_login'
        elif 'sudo' in raw_line and 'COMMAND' in raw_line:
            normalized['event_type'] = 'privilege_escalation'
            normalized['action'] = 'sudo_command'
        elif re.search(r'(GET|POST|HEAD|PUT|DELETE)\s+', raw_line):
            normalized['event_type'] = 'http_request'
            normalized['action'] = 'http_traffic'

        
        # Detect Data Transfers (SCP/SFTP/FTP)
        # Example: "sent 629145600 bytes for /var/data/confidential.tar.gz"
        transfer_match = re.search(r'(sent|transferred)\s+(\d+)\s+bytes.*?(?:for|file)\s+([/\w\._-]+)', raw_line, re.IGNORECASE)
        if transfer_match:
            normalized['event_type'] = 'data_transfer'
            normalized['action'] = 'file_copy'
            normalized['size_bytes'] = int(transfer_match.group(2))
            normalized['file_name'] = transfer_match.group(3)

        return normalized


# ============================================================================
# PHASE 5: ENRICHMENT SERVICE
# ============================================================================
class EnrichmentService:
    """
    Enriches security signals with external threat intelligence:
    - GeoIP data (country, ISP, VPN detection)
    - VirusTotal IP reputation
    - Historical incident memory
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.geoip_cache = {}
        self.vt_cache = {}
    
    async def enrich_ip(self, ip: str) -> dict:
        """
        Comprehensive IP enrichment with GeoIP and VirusTotal data.
        """
        enrichment = {
            'geoip': {},
            'virustotal': {},
            'is_vpn': False,
            'is_hosting': False,
            'is_malicious': False,
            'reputation_score': 0
        }
        
        # Skip private/local IPs
        if ip.startswith(('127.', '10.', '192.168.', '172.16.', '::1', 'Local')):
            enrichment['geoip'] = {'country': 'Local', 'isp': 'Private Network'}
            return enrichment
        
        # GeoIP Lookup
        if Config.ENABLE_GEOIP:
            enrichment['geoip'] = await self._get_geoip_data(ip)
            enrichment['is_vpn'] = enrichment['geoip'].get('proxy', False)
            enrichment['is_hosting'] = enrichment['geoip'].get('hosting', False)
        
        # VirusTotal Lookup
        if Config.ENABLE_VIRUSTOTAL and Config.VIRUSTOTAL_API_KEY != 'your_virustotal_key_here':
            enrichment['virustotal'] = await self._get_virustotal_data(ip)
            enrichment['is_malicious'] = enrichment['virustotal'].get('malicious', 0) >= Config.MALICIOUS_IP_SCORE_THRESHOLD
            enrichment['reputation_score'] = enrichment['virustotal'].get('malicious', 0)
        
        return enrichment
    
    async def _get_geoip_data(self, ip: str) -> dict:
        """
        Query ip-api.com for GeoIP data (free tier: 45 req/min)
        """
        if ip in self.geoip_cache:
            return self.geoip_cache[ip]
        
        try:
            url = Config.GEOIP_API_URL.format(ip=ip)
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 'success':
                            result = {
                                'country': data.get('country', 'Unknown'),
                                'country_code': data.get('countryCode', 'XX'),
                                'city': data.get('city', 'Unknown'),
                                'isp': data.get('isp', 'Unknown'),
                                'org': data.get('org', 'Unknown'),
                                'proxy': data.get('proxy', False),
                                'hosting': data.get('hosting', False)
                            }
                            self.geoip_cache[ip] = result
                            return result
        except Exception as e:
            print(f"GeoIP lookup failed for {ip}: {e}")
        
        return {'country': 'Unknown', 'country_code': 'XX', 'isp': 'Unknown'}
    
    async def _get_virustotal_data(self, ip: str) -> dict:
        """
        Query VirusTotal API v3 for IP reputation
        """
        if ip in self.vt_cache:
            return self.vt_cache[ip]
        
        try:
            url = Config.VIRUSTOTAL_IP_URL.format(ip=ip)
            headers = {'x-apikey': Config.VIRUSTOTAL_API_KEY}
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                        result = {
                            'malicious': stats.get('malicious', 0),
                            'suspicious': stats.get('suspicious', 0),
                            'harmless': stats.get('harmless', 0),
                            'undetected': stats.get('undetected', 0)
                        }
                        self.vt_cache[ip] = result
                        return result
        except Exception as e:
            print(f"VirusTotal lookup failed for {ip}: {e}")
        
        return {'malicious': 0, 'suspicious': 0, 'harmless': 0, 'undetected': 0}
    
    async def get_incident_history(self, ip: str, user: str) -> list:
        """
        Query incident_memory for historical context
        """
        if not Config.ENABLE_INCIDENT_MEMORY:
            return []
        
        try:
            # Query for both IP and user history
            stmt = select(IncidentMemory).where(
                (IncidentMemory.entity_value == ip) | 
                (IncidentMemory.entity_value == user)
            ).limit(5)
            result = await self.session.execute(stmt)
            incidents = result.scalars().all()
            
            return [{
                'type': inc.entity_type,
                'value': inc.entity_value,
                'feedback_score': inc.feedback_score,
                'last_seen': inc.last_seen.isoformat() if inc.last_seen else None
            } for inc in incidents]
        except Exception as e:
            print(f"Incident memory lookup failed: {e}")
            return []


# ============================================================================
# PHASE 6 & 7: ADVANCED SCORING SYSTEM
# ============================================================================
class AnomalyScorer:
    """
    6-Rule evidence-based scoring system with taint-aware context.
    """
    
    @staticmethod
    async def calculate_score(
        event_count: int,
        target_user: str,
        enrichment: dict,
        session: AsyncSession,
        event_type: str = 'unknown',
        anomaly_result: dict = None
    ) -> dict:
        """
        Calculate comprehensive anomaly score based on 6 rules.
        """
        score = 0
        evidence = []
        
        # Rule 1: High Attempt Count (0-20 points)
        if event_count > Config.HIGH_ATTEMPT_THRESHOLD:
            rule1_score = min(20, event_count)
            score += rule1_score
            evidence.append(f"High attempt count: {event_count} events (+{rule1_score})")

        # Rule 7: Statistical Anomaly (Phase 9)
        if anomaly_result and anomaly_result.get('is_anomaly'):
            z_score = anomaly_result.get('z_score', 0)
            score += 25  # Medium-High impact
            evidence.append(f"Statistical Deviation: {anomaly_result['description']} (+25)")

        # Rule: Volumetric Flood (DDoS)
        if event_count > 100:
            score += 60
            evidence.append(f"Volumetric flood detected: {event_count} events (+60)")
        
        # Rule: Data Exfiltration (Specific Boost)
        if event_type == 'data_transfer':
            score += 50
            evidence.append(f"Data exfiltration activity detected (+50)")

        # Rule: Sustained Authentication Attack (Boost for Low-Volume Brute Force)
        if event_type == 'auth_failure' and event_count > 10:
            score += 50
            evidence.append(f"Sustained brute force pattern detected (+50)")
        


        # Rule 2: Critical Target (Phase 7 - Taint-Aware)
        asset_multiplier = 1.0
        try:
            stmt = select(Asset).where(Asset.username == target_user)
            result = await session.execute(stmt)
            asset = result.scalars().first()
            
            if asset:
                if asset.criticality == 'CRITICAL':
                    score += 30
                    asset_multiplier = 1.5
                    evidence.append(f"Critical asset targeted: {target_user} (+30)")
                elif asset.criticality == 'HIGH':
                    score += 20
                    asset_multiplier = 1.2
                    evidence.append(f"High-value asset targeted: {target_user} (+20)")
                
                # Rule 3: No MFA Enabled
                if not asset.mfa_status:
                    score += 15
                    evidence.append(f"Target lacks MFA protection (+15)")
        except Exception as e:
            print(f"Asset lookup failed for {target_user}: {e}")
        
        # Rule 4: Suspicious Geography
        country_code = enrichment.get('geoip', {}).get('country_code', 'XX')
        if country_code in Config.CRITICAL_GEOGRAPHY:
            score += 20
            evidence.append(f"Attack from high-risk country: {country_code} (+20)")
        
        # Rule 5: VPN/Anonymizer Usage
        if enrichment.get('is_vpn') or enrichment.get('is_hosting'):
            score += 10
            evidence.append(f"VPN/Hosting provider detected (+10)")
        
        # Rule 6: Known Malicious IP
        if enrichment.get('is_malicious'):
            malicious_count = enrichment.get('reputation_score', 0)
            score += 25
            evidence.append(f"Malicious IP: {malicious_count} vendors flagged (+25)")
        
        # Calculate final confidence (0-1 scale)
        raw_confidence = min(0.99, score / 120)
        final_confidence = min(0.99, raw_confidence * asset_multiplier)
        
        # Determine risk level
        if final_confidence >= 0.80:
            risk_level = 'CRITICAL'
        elif final_confidence >= 0.60:
            risk_level = 'HIGH'
        elif final_confidence >= 0.40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'raw_score': score,
            'confidence': final_confidence,
            'risk_level': risk_level,
            'evidence': evidence,
            'asset_multiplier': asset_multiplier
        }


# ============================================================================
# PHASE 4: TIME-WINDOW AGGREGATION
# ============================================================================
class AggregationEngine:
    """
    Aggregates events into time windows and detects escalation patterns.
    """
    
    @staticmethod
    def aggregate_events(events: list, window_minutes: int = 5) -> dict:
        """
        Bucket events into time windows and detect escalation.
        
        Returns aggregated events grouped by (source_ip, target_user, event_type)
        """
        # Group by composite key
        buckets = defaultdict(lambda: {
            'events': [],
            'timestamps': [],
            'count': 0,
            'total_size_bytes': 0,
            'files': set()
        })
        
        for event in events:
            key = (
                event.get('source_ip', 'unknown'),
                event.get('target_user', 'unknown'),
                event.get('event_type', 'unknown')
            )
            buckets[key]['events'].append(event)
            buckets[key]['timestamps'].append(event.get('timestamp', datetime.utcnow()))
            buckets[key]['count'] += 1
            
            if 'size_bytes' in event:
                buckets[key]['total_size_bytes'] += event['size_bytes']
            if 'file_name' in event:
                buckets[key]['files'].add(event['file_name'])
        
        # Detect escalation patterns
        aggregated = []
        for (src_ip, target, evt_type), data in buckets.items():
            # Calculate time range
            timestamps = sorted(data['timestamps'])
            time_range = {
                'start': timestamps[0].isoformat() if timestamps else None,
                'end': timestamps[-1].isoformat() if timestamps else None,
                'duration_seconds': (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) > 1 else 0
            }
            
            # Detect escalation (increasing pattern)
            escalation_detected = False
            if len(timestamps) >= 3:
                # Simple escalation: check if events are increasing
                mid_count = len([t for t in timestamps if t < timestamps[len(timestamps)//2]])
                late_count = len(timestamps) - mid_count
                if late_count > mid_count * Config.ESCALATION_THRESHOLD:
                    escalation_detected = True
            
            aggregated.append({
                'source_ip': src_ip,
                'target_user': target,
                'event_type': evt_type,
                'event_count': data['count'],
                'time_range': time_range,
                'escalation_detected': escalation_detected,
                'compression_ratio': data['count'],  # Number of logs compressed into 1 signal
                'total_size_bytes': data.get('total_size_bytes', 0),
                'files_accessed': list(data.get('files', []))
            })
        
        return aggregated


# ============================================================================
# MAIN ANALYZER WITH ALL 8 PHASES INTEGRATED
# ============================================================================
class DynamicLogAnalyzer:
    def __init__(self):
        self.raw_events = []
        self.ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        
        # Phase 2: Drain3 Template Mining
        config = TemplateMinerConfig()
        self.miner = TemplateMiner(config=config)
        self.templates = {}
    
    def process_line(self, line: str):
        """
        Phase 1 & 2: Ingest and parse raw log lines
        Phase 3: Normalize fields
        """
        # Phase 2: Extract template
        result = self.miner.add_log_message(line)
        template_id = result.get('cluster_id', 0)
        
        if result["change_type"] == "cluster_created":
            self.templates[template_id] = result["template_mined"]
        
        # Phase 3: Normalize
        normalized = FieldNormalizer.normalize_log_entry(line)
        normalized['template_id'] = template_id
        normalized['timestamp'] = datetime.utcnow()
        
        self.raw_events.append(normalized)
    
    async def generate_signals(self, session: AsyncSession) -> list:
        """
        Phase 4-8: Generate enriched, scored, and aggregated signals
        """
        # Phase 4: Aggregate events
        aggregated = AggregationEngine.aggregate_events(
            self.raw_events,
            window_minutes=Config.TIME_WINDOW_MINUTES
        )
        
        # Phase 5: Enrichment Service
        enrichment_svc = EnrichmentService(session)
        
        signals = []
        for agg in aggregated:
            src_ip = agg['source_ip']
            target = agg['target_user']
            count = agg['event_count']
            
            # Skip if no valid IP
            if not src_ip or src_ip == 'unknown':
                continue
            
            # RECLASSIFICATION: Volumetric Flood (Safety Net)
            # If we see > 100 events from one IP and type is unknown, assume flood.
            if count > 100 and agg['event_type'] == 'unknown':
                agg['event_type'] = 'network_flood'

            # Phase 5: Enrich with GeoIP + VirusTotal + History
            enrichment = await enrichment_svc.enrich_ip(src_ip)
            incident_history = await enrichment_svc.get_incident_history(src_ip, target)
            
            # Phase 9: Statistical Anomaly Detection
            # 1. Update Daily Stats (Persist for future learning)
            await AnomalyService.update_stats(session, 'IP', src_ip, count)  # Track IP activity
            if target and target != 'unknown':
                await AnomalyService.update_stats(session, 'USER', target, count) # Track User activity

            # 2. Get Anomaly Score (Check against baseline)
            # Primary check on IP for now, can extend to User
            anomaly_result = await AnomalyService.get_anomaly_score(session, 'IP', src_ip, count)
            
            # Phase 6 & 7: Calculate score with taint-awareness
            scoring = await AnomalyScorer.calculate_score(
                event_count=count,
                target_user=target,
                enrichment=enrichment,
                session=session,
                event_type=agg['event_type'],
                anomaly_result=anomaly_result
            )
            
            # Phase 8: MITRE Mapping
            mitre_id = self._map_to_mitre(agg['event_type'], scoring['risk_level'], enrichment)
            
            # Build comprehensive context
            context_json = {
                'geoip': enrichment['geoip'],
                'virustotal': enrichment['virustotal'],
                'is_vpn': enrichment['is_vpn'],
                'is_malicious': enrichment['is_malicious'],
                'incident_history': incident_history,
                'time_range': agg['time_range'],
                'escalation_detected': agg['escalation_detected'],
                'compression_ratio': agg['compression_ratio'],
                'evidence': scoring['evidence'],
                'raw_score': scoring['raw_score'],
                'asset_multiplier': scoring['asset_multiplier'],
                'template_id': self.raw_events[0].get('template_id') if self.raw_events else None,
                'size_bytes': agg.get('total_size_bytes', 0),
                'file_name': agg.get('files_accessed', [])[0] if agg.get('files_accessed') else 'unknown'
            }
            
            # Create signal
            signal = SecuritySignal(
                attack_type=self._get_attack_type(agg['event_type'], enrichment),
                raw_event_type=agg['event_type'],
                anomaly_score='HIGH' if scoring['confidence'] >= 0.6 else 'MEDIUM' if scoring['confidence'] >= 0.4 else 'LOW',
                confidence=scoring['confidence'],
                risk_level=scoring['risk_level'],
                mitre_id=mitre_id,
                source_ip=src_ip,
                target_user=target or 'unknown',
                event_count=count,
                reasoning=self._build_reasoning(scoring, enrichment, agg),
                context_json=context_json
            )
            signals.append(signal)
        
        return signals
    
    def _map_to_mitre(self, event_type: str, risk_level: str, enrichment: dict) -> str:
        """
        Phase 8: Dynamic MITRE ATT&CK mapping
        """
        if event_type == 'auth_failure':
            if enrichment.get('is_malicious'):
                return 'T1110.001'  # Brute Force: Password Guessing (with malicious IP)
            return 'T1110'  # Brute Force
        elif event_type == 'privilege_escalation':
            return 'T1548'  # Abuse Elevation Control Mechanism
        elif event_type == 'data_transfer':
            return 'T1048' # Exfiltration Over Alternative Protocol
        elif event_type == 'network_flood':
            return 'T1498' # Network Denial of Service
        elif event_type == 'http_request':
            if risk_level in ['CRITICAL', 'HIGH']:
                return 'T1498'  # Network DoS
            return 'T1595'  # Active Scanning

        else:
            return 'unknown'
    
    def _get_attack_type(self, event_type: str, enrichment: dict) -> str:
        """
        Generate human-readable attack type
        """
        base_type = {
            'auth_failure': 'Authentication Attack',
            'privilege_escalation': 'Privilege Escalation',
            'http_request': 'Network Traffic Anomaly',
            'data_transfer': 'Data Exfiltration Activity',
            'network_flood': 'Volumetric Network Flood',

        }.get(event_type, 'Unknown Activity')
        
        if enrichment.get('is_malicious'):
            return f"{base_type} (Malicious IP)"
        elif enrichment.get('is_vpn'):
            return f"{base_type} (VPN)"
        
        return base_type
    
    def _build_reasoning(self, scoring: dict, enrichment: dict, agg: dict) -> str:
        """
        Build comprehensive reasoning with evidence
        """
        parts = [
            f"Detected {agg['event_count']} events",
            f"Confidence: {scoring['confidence']:.2%}",
            f"Location: {enrichment['geoip'].get('country', 'Unknown')}"
        ]
        
        if agg['escalation_detected']:
            parts.append("ESCALATION PATTERN DETECTED")
        
        if scoring['evidence']:
            parts.append(f"Evidence: {'; '.join(scoring['evidence'][:3])}")
        
        return " | ".join(parts)


# ============================================================================
# PREPROCESSOR SERVICE
# ============================================================================
class PreprocessorService:
    @staticmethod
    async def process_file(file_path: str, session: AsyncSession):
        """
        Complete 8-phase processing pipeline
        """
        analyzer = DynamicLogAnalyzer()
        total_lines = 0
        
        import time
        start_time = time.time()
        
        print("Phase 1: Log Ingestion started...")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                total_lines += 1
                analyzer.process_line(line)
                if total_lines % 10000 == 0:
                    print(f"  Processed {total_lines} lines...")
        
        print(f"Phase 1-3 complete. Total lines: {total_lines}")
        print("Phase 4-8: Aggregation, Enrichment, Scoring, MITRE Mapping...")
        
        final_signals = await analyzer.generate_signals(session)
        
        processing_time = time.time() - start_time
        
        compression_ratio = total_lines / len(final_signals) if final_signals else 1
        print(f"[SUCCESS] Generated {len(final_signals)} signals (Compression: {compression_ratio:.1f}x)")
        
        # AGGREGATION MODE: Do not clear old signals
        # await session.execute(delete(SecuritySignal))
        
        # Save new signals
        for s in final_signals:
            session.add(s)
        await session.commit()
        
        print("[SUCCESS] Database commit successful.")
        # Calculate valid events (successfully parsed)
        valid_event_count = sum(1 for e in analyzer.raw_events if e.get('event_type') != 'unknown')

        return final_signals, {
            "total_lines": total_lines,
            "valid_events": valid_event_count,
            "signals_generated": len(final_signals),
            "compression_ratio": f"{compression_ratio:.1f}x",
            "processing_time_ms": round(processing_time * 1000, 2)
        }
