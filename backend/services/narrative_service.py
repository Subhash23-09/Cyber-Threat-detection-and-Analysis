from services.llm_service import LLMService

class NarrativeService:
    @staticmethod
    def generate_storyline(agent_reports, decision, context):
        """
        Generates a chronological 'Attack Story' using all telemetry gathered.
        """
        prompt_template = """
            You are the "Security Narrative Architect".
            Transform the following technical telemetry into a clear, cohesive, and chronological "Attack Story" for an executive audience.
            
            1. DISCOVERY (Step 2 Signals) - Be sure to mention the GEOGRAPHICAL LOCATION (Country) of the attackers if available.
            2. INVESTIGATION (Multiple Agent Findings)
            3. VERDICT (Executive Verdict)
            4. MITIGATION (Response Actions)
            
            TECHNICAL CONTEXT:
            Signals Summary:
            {signals}
            
            All Forensic Findings:
            {findings}
            
            Executive Verdict:
            {verdict}
            
            Task: Write a 3-paragraph narrative:
            - Paragraph 1: How the anomaly was first detected across different vectors. Mention specific IPs and their locations (Countries).
            - Paragraph 2: Comprehensive overview of what all specialized agents uncovered during forensics.
            - Paragraph 3: The unified strategic decision and the multi-layer path to remediation.
            
            CRITICAL: Do NOT mention "CISO" or "Chief Information Security Officer" in the output. Use terms like "Executive Verdict", "System Response", or "Defense Strategy".
            
            Maintain a professional, authoritative tone. Avoid jargon where possible. 
            Ensure the story feels like a single event with multiple facets rather than separate incidents.
            """
            
        # Extract relevant bits for the prompt and format them nicely
        raw_signals = context.get('short_term', {}).get('active_context', [])[:15]
        formatted_signals = []
        for s in raw_signals:
            country = s.get('context', {}).get('geoip', {}).get('country', 'Unknown Location')
            formatted_signals.append(
                f"- {s.get('created_at', 'Now')}: {s.get('event_type')} from {s.get('actor', {}).get('source_ip')} "
                f"({country}) targeting {s.get('target', {}).get('user')}. Confidence: {s.get('metrics', {}).get('confidence')}%"
            )
        
        # Aggregate findings from all malicious reports
        all_findings = []
        reports_list = list(agent_reports.values()) if isinstance(agent_reports, dict) else [agent_reports]
        
        for r in reports_list:
            verdict = r.get('report', {}).get('verdict', 'BENIGN')
            if verdict == "MALICIOUS":
                agent_name = r.get('agent', 'Unknown Agent')
                agent_findings = r.get('report', {}).get('findings', [])
                for f in agent_findings:
                    if isinstance(f, dict):
                        # Extract location from signal context if available in findings
                        desc = f.get('description', '')
                        all_findings.append(f"{agent_name}: {f.get('title', 'Finding')} - {desc}")
                    else:
                        all_findings.append(f"{agent_name}: {str(f)}")
        
        if decision:
            verdict_text = decision.get('executive_summary', decision.get('reasoning', 'No summary provided'))
        else:
            verdict_text = "Automated analysis completed. Pending final executive review."
        
        input_data = {
            "signals": "\n".join(formatted_signals) if formatted_signals else "No recent signals found.",
            "findings": "\n".join(all_findings) if all_findings else "No malicious findings reported.",
            "verdict": verdict_text
        }
        
        print(f"DEBUG [NarrativeService]: Input data ready. Signals: {len(formatted_signals)}, Findings: {len(all_findings)}")
        return LLMService.stream_decision(prompt_template, input_data)
