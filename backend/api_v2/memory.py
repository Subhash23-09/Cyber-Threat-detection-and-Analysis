from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from models_v2 import IncidentMemory
from sqlalchemy import select

from datetime import datetime

router = APIRouter()

@router.get("/context")
async def get_memory_context():
    async with AsyncSessionLocal() as session:
        from models_v2 import SecuritySignal
        # Fetch latest 20 signals for short-term context
        res = await session.execute(
            select(SecuritySignal).order_by(SecuritySignal.timestamp.desc()).limit(20)
        )
        signals = res.scalars().all()
        
        # 1. Extract Correlation Keys
        actors = {s.source_ip for s in signals if s.source_ip}
        targets = {s.target_user for s in signals if s.target_user and s.target_user != 'unknown'}
        # Use .action as the correlation key for attack types, as it contains the human-readable name
        actions = {s.attack_type for s in signals if s.attack_type}
        actions.update({s.mitre_id for s in signals if s.mitre_id})
        actions.update({s.to_dict().get('action') for s in signals if s.to_dict().get('action')})

        
        long_term = {
            "related_by_actor": [],
            "related_by_target": [],
            "related_by_action": []
            
        }
        
        # 2. Query Long-Term Memory (Correlation Engine)
        if actors or targets or actions:
            all_values = list(actors | targets | actions)
            q = select(IncidentMemory).where(IncidentMemory.entity_value.in_(all_values))
            res_mem = await session.execute(q)
            memories = res_mem.scalars().all()
            
            for mem in memories:
                # Map to format UI expects
                mem_dict = {
                    "type": mem.entity_type,
                    "value": mem.entity_value,
                    "source_ip": mem.entity_value if mem.entity_type == 'ACTOR' else None,
                    "target_user": mem.entity_value if mem.entity_type == 'TARGET' else None,
                    "action": mem.entity_value if mem.entity_type == 'ACTION' else None,
                    "suspected_attack": mem.entity_value if mem.entity_type == 'ACTION' else None,
                    "feedback_score": mem.feedback_score,
                    "last_seen": mem.last_seen.isoformat() if mem.last_seen else None,
                    "created_at": mem.last_seen.isoformat() if mem.last_seen else None,
                    "notes": mem.analyst_notes
                }
                if mem.entity_type == 'ACTOR':
                    long_term["related_by_actor"].append(mem_dict)
                elif mem.entity_type == 'TARGET':
                    long_term["related_by_target"].append(mem_dict)
                elif mem.entity_type == 'ACTION':
                    long_term["related_by_action"].append(mem_dict)

        return {
            "short_term": {
                "active_context": [s.to_dict() for s in signals],
                "session_start": datetime.utcnow().isoformat() + "Z"
            },
            "long_term": long_term
        }

@router.get("/context/{entity_value}")
async def get_entity_context(entity_value: str):
    async with AsyncSessionLocal() as session:
        q = select(IncidentMemory).where(IncidentMemory.entity_value == entity_value).limit(10)
        result = await session.execute(q)
        memories = result.scalars().all()
        return memories

@router.post("/feedback")
async def store_feedback(id: int, score: int, notes: str = None):
    async with AsyncSessionLocal() as session:
        q = select(IncidentMemory).where(IncidentMemory.id == id)
        result = await session.execute(q)
        memory = result.scalars().first()
        if not memory:
            raise HTTPException(status_code=404, detail="Memory entry not found")
        memory.feedback_score = score
        memory.analyst_notes = notes
        await session.commit()
        return {"status": "success"}
