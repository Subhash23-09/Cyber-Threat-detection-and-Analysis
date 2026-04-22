from fastapi import APIRouter, BackgroundTasks
from typing import Optional
from fastapi.responses import StreamingResponse
from services.orchestrator import OrchestratorService
from database import AsyncSessionLocal
import json
import asyncio

router = APIRouter()

@router.post("/orchestrate")
async def orchestrate_incident(signal_id: Optional[int] = None):
    from services.orchestrator import OrchestratorService
    
    if signal_id is not None:
        from tasks import orchestrate_task
        orchestrate_task.delay(signal_id)
        return {"status": "queued", "signal_id": signal_id}
    else:
        # Session-wide orchestration for the dashboard Step 4
        # We run the async cycle adapter
        return await OrchestratorService.run_cycle()

@router.post("/chat_stream")
async def chat_stream(request: Optional[dict] = None):
    # Fetch real context for the stream
    from models_v2 import SecuritySignal
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Get latest 20 signals
        res = await session.execute(select(SecuritySignal).order_by(SecuritySignal.timestamp.desc()).limit(20))
        signals_db = res.scalars().all()
        signals = [s.to_dict() for s in signals_db]
        
        # Mocking long-term context for now or fetch if needed
        context = {
            "short_term": {"active_context": signals},
            "long_term": {}
        }

    async def event_generator():
        # Use the real orchestrator generator
        async for event in OrchestratorService.stream_agent_updates(signals, context):
            # Format as SSE
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
