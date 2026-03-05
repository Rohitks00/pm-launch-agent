import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from pipeline import run_pipeline

TEST_DB = "sqlite:///./test_pipeline.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    kit = models.BrandKit(name="Test Kit", voice_tone="Confident", do_list=[], dont_list=[])
    db.add(kit); db.commit()
    run = models.Run(brand_kit_id=kit.id, input_type="paste", raw_input="PRD text", status="processing", progress={})
    db.add(run); db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

MOCK_BRIEF = {"product_name": "SmartSync", "launch_date": "April 1 2026", "key_features": [], "target_audience": "Enterprise PMs", "launch_goals": "Drive signups", "tone_notes": ""}
MOCK_COPY = {"email": {"subject": "...", "body": "...", "alt_subjects": []}, "landing_page": {"headline": "...", "subheadline": "...", "cta": "..."}, "social": [], "compliance_flags": []}
MOCK_SPECS = {"assets": [{"name": "Hero Banner", "format": "PNG", "dimensions": "1920x1080", "placement": "Homepage", "notes": "..."}]}

@pytest.mark.asyncio
async def test_pipeline_creates_outputs():
    with patch("pipeline.SessionLocal", return_value=TestingSession()), \
         patch("pipeline.run_orchestrator", new_callable=AsyncMock, return_value=MOCK_BRIEF), \
         patch("pipeline.run_copy_agent", new_callable=AsyncMock, return_value=MOCK_COPY), \
         patch("pipeline.run_brief_agent", new_callable=AsyncMock, return_value=MOCK_SPECS):
        await run_pipeline(run_id=1)

    db = TestingSession()
    run = db.query(models.Run).filter(models.Run.id == 1).first()
    brief = db.query(models.StructuredBrief).filter(models.StructuredBrief.run_id == 1).first()
    outputs = db.query(models.Output).filter(models.Output.run_id == 1).all()
    db.close()

    assert run.status == "review"
    assert brief.product_name == "SmartSync"
    assert len(outputs) == 2
    assert {o.output_type for o in outputs} == {"marketing_copy", "asset_specs"}
