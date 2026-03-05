import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_brand_kit_model(db):
    kit = models.BrandKit(name="Test Brand", voice_tone="Confident", do_list=["Be clear"], dont_list=["No jargon"])
    db.add(kit)
    db.commit()
    assert kit.id is not None
    assert kit.name == "Test Brand"

def test_run_model(db):
    kit = models.BrandKit(name="Test Brand")
    db.add(kit)
    db.commit()
    run = models.Run(brand_kit_id=kit.id, input_type="paste", raw_input="some PRD text")
    db.add(run)
    db.commit()
    assert run.id is not None
    assert run.status == "processing"

def test_structured_brief_model(db):
    kit = models.BrandKit(name="Test Brand")
    db.add(kit); db.commit()
    run = models.Run(brand_kit_id=kit.id, input_type="paste", raw_input="text")
    db.add(run); db.commit()
    brief = models.StructuredBrief(
        run_id=run.id,
        product_name="Smart Sync",
        target_audience="Enterprise PMs",
        launch_goals="Drive signups",
        key_features=[{"name": "Sync", "benefit": "saves time"}],
    )
    db.add(brief)
    db.commit()
    assert brief.id is not None

def test_output_model(db):
    kit = models.BrandKit(name="Test Brand")
    db.add(kit); db.commit()
    run = models.Run(brand_kit_id=kit.id, input_type="paste", raw_input="text")
    db.add(run); db.commit()
    output = models.Output(run_id=run.id, output_type="marketing_copy", content={"email": {"subject": "Hello"}})
    db.add(output)
    db.commit()
    assert output.status == "draft"
