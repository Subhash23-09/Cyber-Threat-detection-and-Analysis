from fastapi import APIRouter
from services.mitigation_service import MitigationService
from pydantic import BaseModel

router = APIRouter()

# Schema updated for multi-agent support
class MitigationRequest(BaseModel):
    agent_reports: dict

@router.post("/recommend")
async def recommend_mitigation(request: MitigationRequest):
    return MitigationService.get_playbooks(request.agent_reports)
