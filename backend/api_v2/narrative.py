from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from models_v2 import AttackStoryline
from sqlalchemy import select
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.narrative_service import NarrativeService
from services.memory_store import MemoryService
from datetime import datetime
import json

router = APIRouter()

from typing import Optional

# Schema updated for multi-agent support
class NarrativeRequest(BaseModel):
    agent_reports: dict
    decision: Optional[dict] = None

@router.post("/storylines")
async def generate_storyline(request: NarrativeRequest):
    # Fetch context to feed into the narrative
    context = await MemoryService.get_context()
    
    return StreamingResponse(
        NarrativeService.generate_storyline(request.agent_reports, request.decision, context),
        media_type="text/plain"
    )

@router.get("/report/{signal_id}")
async def get_report(signal_id: int):
    # Simplified placeholder
    return {
        "report_id": f"REP-{signal_id}",
        "status": "Finalized",
        "verdict": "BENIGN"
    }

@router.post("/learn")
async def update_learning(case_data: dict):
    print(f"DEBUG: update_learning called with: {json.dumps(case_data)[:200]}...")
    try:
        case_file = case_data.get("case_file", {})
        investigation = case_file.get("investigation_details", {})
        
        entities = []
        
        # 1. ACTIONS (Attack Types)
        ats = investigation.get("attack_types", [])
        print(f"DEBUG: Found attack_types: {ats}")
        if isinstance(ats, list):
            for at in ats:
                if at: entities.append(('ACTION', at))
                
        # Fallback ACTION (Agent Name)
        agent = investigation.get("agent_deployed")
        print(f"DEBUG: Found agent_deployed: {agent}")
        if agent and agent != 'NONE':
            entities.append(('ACTION', agent))
            
        # 2. ACTORS (IPs)
        actors = investigation.get("involved_trace", [])
        print(f"DEBUG: Found involved_trace: {actors}")
        if isinstance(actors, list):
            for ip in actors:
                if ip and isinstance(ip, str) and len(ip) > 5:
                    entities.append(('ACTOR', ip))
                    
        # 3. TARGETS (Users)
        target = investigation.get("target_user")
        print(f"DEBUG: Found target_user: {target}")
        if target and target.lower() != 'none':
            entities.append(('TARGET', target))
            
        print(f"DEBUG: Total entities to index: {len(entities)}")
        
        saved_count = 0
        async with AsyncSessionLocal() as session:
            from models_v2 import IncidentMemory
            
            # Deduplicate entities before saving
            for e_type, e_val in set(entities):
                if not e_val or e_val.lower() == 'unknown':
                    continue
                    
                print(f"DEBUG: Committing {e_type} | {e_val}")
                mem = IncidentMemory(
                    entity_type=e_type,
                    entity_value=str(e_val),
                    incident_data=case_file,
                    feedback_score=1,
                    analyst_notes=f"Auto-learned from verified pattern",
                    last_seen=datetime.utcnow()
                )
                session.add(mem)
                saved_count += 1
                
            await session.commit()
            print(f"DEBUG: Commit successful. Saved {saved_count} rows.")
        
        return {
            "status": "intelligence updated", 
            "total_related_cases": saved_count,
            "message": f"Assimilated {saved_count} memory fragments."
        }
    except Exception as e:
        print(f"ERROR in update_learning: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }
