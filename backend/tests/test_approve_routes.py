import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models

TEST_DB = "sqlite:///./test_approve.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    kit = models.BrandKit(name="Kit")
    db.add(kit); db.commit()
    run = models.Run(brand_kit_id=kit.id, input_type="paste", raw_input="text", status="review", progress={})
    db.add(run); db.commit()
    output = models.Output(run_id=run.id, output_type="marketing_copy", content={"email": {}})
    db.add(output); db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_approve_output():
    response = client.post("/api/outputs/1/approve", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_reject_with_feedback():
    response = client.post("/api/outputs/1/approve", json={"status": "rejected", "feedback": "Too long"})
    assert response.status_code == 200
    assert response.json()["feedback"] == "Too long"

def test_invalid_status_rejected():
    response = client.post("/api/outputs/1/approve", json={"status": "invalid"})
    assert response.status_code == 422
