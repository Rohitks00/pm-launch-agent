import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

TEST_DB = "sqlite:///./test_bk.db"
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
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_create_brand_kit():
    response = client.post("/api/brand-kit", json={
        "name": "Test Brand",
        "voice_tone": "Confident",
        "do_list": ["Be clear"],
        "dont_list": ["No jargon"]
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Test Brand"
    assert response.json()["id"] is not None

def test_get_brand_kit():
    client.post("/api/brand-kit", json={"name": "Test Brand"})
    response = client.get("/api/brand-kit")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Brand"

def test_get_brand_kit_not_found():
    response = client.get("/api/brand-kit")
    assert response.status_code == 404

def test_update_brand_kit():
    client.post("/api/brand-kit", json={"name": "Test Brand"})
    response = client.put("/api/brand-kit", json={"name": "Updated Brand", "voice_tone": "Bold"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Brand"
    assert response.json()["voice_tone"] == "Bold"
