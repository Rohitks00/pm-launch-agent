from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(tags=["Brand Kit"])

@router.post("/api/brand-kit", response_model=schemas.BrandKitOut)
def create_brand_kit(kit: schemas.BrandKitCreate, db: Session = Depends(get_db)):
    if db.query(models.BrandKit).first():
        raise HTTPException(status_code=400, detail="Brand kit already exists. Use PUT to update.")
    db_kit = models.BrandKit(**kit.model_dump())
    db.add(db_kit)
    db.commit()
    db.refresh(db_kit)
    return db_kit

@router.get("/api/brand-kit", response_model=schemas.BrandKitOut)
def get_brand_kit(db: Session = Depends(get_db)):
    kit = db.query(models.BrandKit).first()
    if not kit:
        raise HTTPException(status_code=404, detail="No brand kit configured")
    return kit

@router.put("/api/brand-kit", response_model=schemas.BrandKitOut)
def update_brand_kit(kit: schemas.BrandKitCreate, db: Session = Depends(get_db)):
    existing = db.query(models.BrandKit).first()
    if not existing:
        raise HTTPException(status_code=404, detail="No brand kit found")
    for key, value in kit.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing
