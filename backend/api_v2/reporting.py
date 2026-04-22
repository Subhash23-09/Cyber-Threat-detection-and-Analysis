from fastapi import APIRouter
from services.reporting_service import ReportingService
from pydantic import BaseModel

router = APIRouter()

# Schema updated for multi-agent support
from typing import Optional

class ReportRequest(BaseModel):
    agent_reports: dict
    decision: Optional[dict] = None

@router.post("/report")
async def generate_report(request: ReportRequest):
    return await ReportingService.generate_case_file(request.agent_reports, request.decision)
