import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models

TEST_DB = "sqlite:///./test_runs.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    kit = models.BrandKit(name="Test Kit")
    db.add(kit); db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_run_paste():
    response = client.post("/api/runs", json={"brand_kit_id": 1, "raw_input": "# Feature Launch\n\nPRD text."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["input_type"] == "paste"

def test_list_runs():
    client.post("/api/runs", json={"brand_kit_id": 1, "raw_input": "PRD"})
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_run():
    resp = client.post("/api/runs", json={"brand_kit_id": 1, "raw_input": "PRD"})
    run_id = resp.json()["id"]
    response = client.get(f"/api/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["id"] == run_id

def test_get_run_not_found():
    response = client.get("/api/runs/9999")
    assert response.status_code == 404
