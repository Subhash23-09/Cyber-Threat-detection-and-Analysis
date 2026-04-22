from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
import os
import time

router = APIRouter()

@router.post("/process/{filename}")
async def process_log(filename: str):
    file_path = os.path.join(os.getcwd(), 'uploads', filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    # Trigger Celery task or background task
    # For now, we use the process_log_task defined in main.py
    # We pass a simple dict to emulate the existing expected input
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_system": "manual_trigger",
        "raw_message": f"Processing file: {filename}"
    }
    
    # In tasks.py, process_file_task is better for files
    from tasks import run_process_file
    result = await run_process_file(file_path, "uploaded_file")
    
    return {
        "message": "Processing complete",
        "filename": filename,
        "stats": result.get("stats", {}),
        "signals_count": result.get("signals_count", 0)
    }

@router.get("/signals")
async def get_signals():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from models_v2 import SecuritySignal
        q = select(SecuritySignal).order_by(SecuritySignal.timestamp.desc()).limit(100)
        result = await session.execute(q)
        signals = result.scalars().all()
        return [s.to_dict() for s in signals]
@router.post("/clear_session")
async def clear_session():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        from models_v2 import SecuritySignal
        from services.memory_store import MemoryService
        
        # 1. Clear signals
        await session.execute(delete(SecuritySignal))
        await session.commit()
        
        # 2. Clear memory
        MemoryService.clear_short_term()
        
        return {"message": "Session cleared successfully"}
