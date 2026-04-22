from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, BackgroundTasks
from pydantic import ValidationError
from typing import Optional
from config import Config
from api_v2.schemas import LogBatch
from celery_app import celery_app
import uuid

router = APIRouter()

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != Config.INGESTION_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": file_path,
            "size": os.path.getsize(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/push", status_code=202)
async def push_logs(batch: LogBatch, api_key: str = Depends(verify_api_key)):
    """
    High-scale / batched log ingestion endpoint.
    Push logs to Celery for async processing.
    """
    job_id = str(uuid.uuid4())
    
    # Push to Celery
    task = celery_app.send_task(
        "process_log_batch_task",
        args=[batch.model_dump(), {"job_id": job_id, "ingested_at": datetime.utcnow().isoformat()}]
    )
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "task_id": task.id,
        "message": f"Queued {len(batch.logs)} logs for processing."
    }
