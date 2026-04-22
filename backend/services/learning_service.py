from models import db
from sqlalchemy import text
import json
from datetime import datetime

class LearningService:
    @staticmethod
    def learn_from_incident(case_file):
        """
        Indexes a confirmed incident into the 'incident_memory' table (V2).
        Extracts ACTOR, TARGET, and ACTION entities for correlation.
        """
        try:
            # Extract key metadata
            investigation = case_file.get('investigation_details', {})
            verdict_data = case_file.get('executive_verdict', {})
            
            # 1. Identify Entities
            entities = []
            
            # ACTIONS (Attack Types from signals)
            # This ensures we match "Authentication Attack (Malicious IP)" exactly
            ats = investigation.get('attack_types', [])
            if isinstance(ats, list):
                for at in ats:
                    if at:
                        entities.append(('ACTION', at))
            
            # Fallback/Legacy ACTION (Agent Name)
            agent = investigation.get('agent_deployed')
            if agent and agent != 'NONE':
                entities.append(('ACTION', agent))
            
            # ACTORS (IPs)
            actors = investigation.get('involved_trace', [])
            if isinstance(actors, list):
                for ip in actors:
                    if ip and isinstance(ip, str) and len(ip) > 5:
                        entities.append(('ACTOR', ip))
            
            # TARGETS (Users)
            user = investigation.get('target_user') or \
                   case_file.get('target', {}).get('user') or \
                   verdict_data.get('target_user')
                   
            if user and user.lower() != 'none':
                entities.append(('TARGET', user))

            saved_count = 0
            incident_data_json = json.dumps(case_file)
            
            # We use a set to avoid duplicates
            for e_type, e_val in set(entities):
                if not e_val or e_val.lower() == 'unknown':
                    continue
                    
                # Insert or Update (for MVP we just Insert)
                sql = text("""
                    INSERT INTO incident_memory 
                    (entity_type, entity_value, incident_data, feedback_score, analyst_notes, last_seen)
                    VALUES (:etype, :eval, :data, :score, :notes, :seen)
                """)
                
                db.session.execute(sql, {
                    'etype': e_type,
                    'eval': str(e_val),
                    'data': incident_data_json,
                    'score': 1,
                    'notes': verdict_data.get('executive_summary', 'Confirmed Malicious'),
                    'seen': datetime.utcnow()
                })
                saved_count += 1
            
            db.session.commit()
            
            return {
                "status": "success",
                "message": f"Assimilated {saved_count} new memory entities.",
                "total_related_cases": saved_count
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"Learning Error: {e}")
            raise e
