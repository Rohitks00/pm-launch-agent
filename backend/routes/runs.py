from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, file_extractor
from pipeline import run_pipeline

router = APIRouter(tags=["Runs"])

@router.post("/api/runs", response_model=schemas.RunOut)
async def create_run_paste(req: schemas.RunCreatePaste, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = models.Run(
        brand_kit_id=req.brand_kit_id,
        input_type="paste",
        raw_input=req.raw_input,
        status="processing",
        progress={"orchestrator": "pending", "copy_agent": "pending", "brief_agent": "pending"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(run_pipeline, run.id)
    return run

@router.post("/api/runs/upload", response_model=schemas.RunOut)
async def create_run_upload(background_tasks: BackgroundTasks, brand_kit_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    raw_input = file_extractor.extract_text_from_bytes(content, file.filename)
    run = models.Run(
        brand_kit_id=brand_kit_id,
        input_type="file",
        raw_input=raw_input,
        filename=file.filename,
        status="processing",
        progress={"orchestrator": "pending", "copy_agent": "pending", "brief_agent": "pending"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(run_pipeline, run.id)
    return run

@router.get("/api/runs", response_model=List[schemas.RunOut])
def list_runs(db: Session = Depends(get_db)):
    return db.query(models.Run).order_by(models.Run.created_at.desc()).all()

@router.get("/api/runs/{run_id}", response_model=schemas.RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(models.Run).filter(models.Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/api/runs/{run_id}/brief", response_model=schemas.StructuredBriefOut)
def get_brief(run_id: int, db: Session = Depends(get_db)):
    brief = db.query(models.StructuredBrief).filter(models.StructuredBrief.run_id == run_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not ready yet")
    return brief

@router.put("/api/runs/{run_id}/brief", response_model=schemas.StructuredBriefOut)
def update_brief(run_id: int, update: schemas.StructuredBriefUpdate, db: Session = Depends(get_db)):
    brief = db.query(models.StructuredBrief).filter(models.StructuredBrief.run_id == run_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    for key, value in update.model_dump(exclude_none=True).items():
        setattr(brief, key, value)
    db.commit()
    db.refresh(brief)
    return brief

@router.get("/api/runs/{run_id}/outputs", response_model=List[schemas.OutputOut])
def get_outputs(run_id: int, db: Session = Depends(get_db)):
    return db.query(models.Output).filter(models.Output.run_id == run_id).all()
