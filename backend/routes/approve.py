from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional
from database import get_db
import models, schemas
from pipeline import regenerate_output

router = APIRouter(tags=["Approve"])

class ApproveRequest(BaseModel):
    status: str
    feedback: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v not in ("approved", "rejected"):
            raise ValueError("status must be 'approved' or 'rejected'")
        return v

@router.post("/api/outputs/{output_id}/approve", response_model=schemas.OutputOut)
async def approve_output(output_id: int, req: ApproveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    output = db.query(models.Output).filter(models.Output.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    output.status = req.status
    if req.feedback:
        output.feedback = req.feedback
    db.commit()
    db.refresh(output)
    if req.status == "rejected" and req.feedback:
        background_tasks.add_task(regenerate_output, output_id, req.feedback)
    return output
