from models import db, Signal
from datetime import datetime
import json

class MemoryService:
    # Short-term memory (Session cache) - singleton pattern for MVP
    _short_term_store = {
        "active_context": [],
        "session_start": str(datetime.utcnow())
    }

    @classmethod
    def clear_short_term(cls):
        """
        Resets the short-term memory store.
        """
        cls._short_term_store = {
            "active_context": [],
            "session_start": str(datetime.utcnow())
        }
        print("[MemoryService] Short-term memory reset.")

    @classmethod
    def update_short_term(cls, signals):

        """
        Updates short-term memory with new signals from the current session.
        Limits to most recent 100 signals to prevent memory bloat.
        """
        # Convert signals to dicts and add to context
        new_signals = [s.to_dict() for s in signals]
        cls._short_term_store["active_context"].extend(new_signals)
        
        # Keep only the most recent 100 signals to prevent payload size issues
        if len(cls._short_term_store["active_context"]) > 100:
            cls._short_term_store["active_context"] = cls._short_term_store["active_context"][-100:]
            print(f"[MemoryService] Trimmed short-term memory to 100 most recent signals")
        
        return cls._short_term_store

    @classmethod
    async def get_context(cls):
        """
        Retrieves complete context (Short Term + Long Term Query) based on 6-Factor Model.
        """
        print("[MemoryService] get_context() called")
        try:
            # 1. Short Term - Fetch from DB to ensure cross-process consistency
            from models_v2 import SecuritySignal
            from database import AsyncSessionLocal
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                # Get last 50 signals
                result = await session.execute(select(SecuritySignal).order_by(SecuritySignal.timestamp.desc()).limit(50))
                signals_db = result.scalars().all()
                active_signals = [s.to_dict() for s in signals_db]
                
            short_term = {
                "active_context": active_signals,
                "session_start": cls._short_term_store["session_start"]
            }
            # Update local cache just in case
            cls._short_term_store["active_context"] = active_signals
            print(f"[MemoryService] Active signals count: {len(active_signals)}")
            
            if not active_signals:
                print("[MemoryService] No active signals, returning empty context")
                return {"short_term": short_term, "long_term": {}}

            # Extract search keys from active session (limit to top 5 most frequent to avoid performance issues)
            print("[MemoryService] Extracting actors, targets, actions...")
            from collections import Counter
            
            # Count occurrences
            actor_ips = [s.get('actor', {}).get('source_ip') for s in active_signals if s.get('actor', {}).get('source_ip')]
            target_users = [s.get('target', {}).get('user') for s in active_signals if s.get('target', {}).get('user')]
            action_types = [s.get('action') for s in active_signals if s.get('action')]
            
            # Get top 5 most frequent
            actors = set([ip for ip, count in Counter(actor_ips).most_common(5)])
            targets = set([user for user, count in Counter(target_users).most_common(5)])
            actions = set([action for action, count in Counter(action_types).most_common(5)])
            
            print(f"[MemoryService] Top entities - {len(actors)} actors, {len(targets)} targets, {len(actions)} actions")

            long_term_context = {
                "related_by_actor": [],
                "related_by_target": [],
                "related_by_action": []
            }
            
            # 2. Long Term - Query DB using Async Session (Re-using session would be ideal, but for now we create a new one or better yet, do it all in one block)
            # We already have active_signals, so we can start a new async session for history
            print("[MemoryService] Querying database for historical context...")
            
            async with AsyncSessionLocal() as session:
                 # Helper to fetch and format asynchronously
                async def fetch_history_async(entity_type, values, limit=5):
                    try:
                        from models_v2 import IncidentMemory
                        stmt = select(IncidentMemory).where(
                            (IncidentMemory.entity_type == entity_type) & 
                            (IncidentMemory.entity_value.in_(values))
                        ).order_by(IncidentMemory.last_seen.desc()).limit(limit)
                        result = await session.execute(stmt)
                        results = result.scalars().all()
                        return [{
                            "type": r.entity_type,
                            "value": r.entity_value,
                            "source_ip": r.entity_value if r.entity_type == 'ACTOR' else None,
                            "target_user": r.entity_value if r.entity_type == 'TARGET' else None,
                            "action": r.entity_value if r.entity_type == 'ACTION' else None,
                            "suspected_attack": r.entity_value if r.entity_type == 'ACTION' else None,
                            "feedback_score": r.feedback_score,
                            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                            "created_at": r.last_seen.isoformat() if r.last_seen else None,
                            "notes": r.analyst_notes
                        } for r in results]
                    except Exception as e:
                        print(f"[MemoryService] fetch_history_async error: {e}")
                        return []

                # A. By Actor (Source IP)
                if actors:
                    long_term_context["related_by_actor"] = await fetch_history_async('ACTOR', actors)

                # B. By Target (User)
                if targets:
                    long_term_context["related_by_target"] = await fetch_history_async('TARGET', targets)

                # C. By Action (Attack Type)
                if actions:
                    long_term_context["related_by_action"] = await fetch_history_async('ACTION', actions)

            print(f"[MemoryService] Long-term context: {len(long_term_context['related_by_actor'])} by actor, {len(long_term_context['related_by_target'])} by target, {len(long_term_context['related_by_action'])} by action")
            print("[MemoryService] Returning context")
            
            return {
                "short_term": short_term,
                "long_term": long_term_context
            }
        except Exception as e:
            print(f"[MemoryService] CRITICAL ERROR in get_context: {e}")
            import traceback
            traceback.print_exc()
            raise

