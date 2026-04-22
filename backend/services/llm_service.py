import os
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class LLMService:
    @staticmethod
    def get_llm():
        """
        Returns a configured LangChain ChatGroq instance.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        
        return ChatGroq(
            temperature=0, 
            groq_api_key=api_key, 
            model_name="llama-3.3-70b-versatile"
        )

    @staticmethod
    def stream_decision(prompt_template, input_variables):
        """
        Streams the response from the LLM.
        """
        llm = LLMService.get_llm()
        
        if not llm:
            # Mock Stream (Simulation Mode)
            mock_text = '{"executive_summary": "System detected a simulated threat. No immediate action required.", "action_items": ["Review security configuration", "Monitor logs for deviations"], "defensibility_score": 88}'

            for char in mock_text:
                time.sleep(0.05)
                yield char
            return

        try:
            print(f"DEBUG [LLMService]: Starting stream for template...")
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm | StrOutputParser()
            
            for chunk in chain.stream(input_variables):
                yield chunk
                
        except Exception as e:
            print(f"ERROR [LLMService]: Stream failed: {str(e)}")
            yield f'{{"error": "{str(e)}"}}'

    @staticmethod
    def route_decision(context):
        """
        Principal Agent that decides which specific Attack Agent to verify the signals.
        """
        llm = LLMService.get_llm()
        
        # MOCK FALLBACK (If no API key or API fails)
        if not llm:
            print("WARNING: No GROQ_API_KEY found. Using Mock LLM response.")
            time.sleep(1.5) # Simulate thinking
            return {
                "decision": "DEPLOY_AUTH_AGENT",
                "reasoning": "The detected pattern (multiple failed passwords from single IP) matches Mitre T1110.001. Requires specialized validation.",
                "confidence": "HIGH"
            }

        try:
            # Real LLM Call using LangChain
            prompt = ChatPromptTemplate.from_template("""
            You are the "Decision Router" for an Autonomous Cyber Defense system.
            Analyze the following security context and decide which specialized agent to deploy.
            
            CONTEXT:
            {context}
            
            AVAILABLE AGENTS:
            1. AUTH_AGENT (For brute force, login anomalies)
            2. DDOS_AGENT (For volumetric network anomalies, potential DoS/DDoS attacks)
            3. EXFIL_AGENT (For unauthorized data transfer, large outbound flows)
            4. MITM_AGENT (For SSL/ARP spoofing, man-in-the-middle deviations)
            5. IGNORE (For clear false positives or benign activities)
            
            RESPONSE FORMAT (JSON only):
            {{
                "decision": "AGENT_NAME",
                "reasoning": "Brief explanation",
                "confidence": "HIGH/MEDIUM/LOW"
            }}

            """)
            
            chain = prompt | llm | StrOutputParser()
            response_str = chain.invoke({"context": str(context)})
            
            # Simple cleanup to ensure we get a dict/json (Naive for MVP)
            # In prod, use JsonOutputParser
            import json
            import re
            
            try:
                # remove any potential markdown code blocks
                clean_str = response_str.replace('```json', '').replace('```', '').strip()
                # Find the first { and last }
                start = clean_str.find('{')
                end = clean_str.rfind('}') + 1
                if start != -1 and end != -1:
                    clean_str = clean_str[start:end]
                    
                return json.loads(clean_str)
            except Exception as parse_e:
                print(f"JSON Parse Error: {parse_e}")
                return {
                    "decision": "ERROR_PARSING_LLM",
                    "reasoning": response_str[:200], # Truncate for safety
                    "confidence": "LOW"
                }

        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "decision": "FALLBACK_ERROR",
                "reasoning": f"LLM failed: {str(e)}",
                "confidence": "LOW"
            }

    @staticmethod
    def analyze_logs(log_snippet):
        """
        Deep semantic analysis of raw log snippets to identify logical attacks.
        """
        llm = LLMService.get_llm()
        if not llm:
            return []

        try:
            prompt = ChatPromptTemplate.from_template("""
            You are a Senior Forensic Security Analyst. 
            Analyze the following raw log snippet and identify any logical security attacks or suspicious patterns.
            
            LOG SNIPPET:
            {logs}
            
            Analyze for:
            - Privilege Escalation (Sudo abuse, shell escapes)
            - Semantic anomalies (Base64 encoding, unusual command patterns)
            - Lateral movement or Exfiltration attempts
            
            RESPONSE FORMAT (JSON Array only):
            [
                {{
                    "event_type": "logical_attack",
                    "suspected_attack": "Description of attack",
                    "mitre_id": "TXXXX",
                    "confidence": 0-100,
                    "reasoning": "Deep forensic explanation"
                }}
            ]
            
            If no attacks are found, return an empty array [].
            """)
            
            chain = prompt | llm | StrOutputParser()
            response_str = chain.invoke({"logs": log_snippet})
            
            import json
            import re
            
            clean_str = response_str.replace('```json', '').replace('```', '').strip()
            start = clean_str.find('[')
            end = clean_str.rfind(']') + 1
            if start != -1 and end != -1:
                return json.loads(clean_str[start:end])
            return []

        except Exception as e:
            print(f"LLM Analyze Logs Error: {e}")
            return []
