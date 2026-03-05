from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
import models  # noqa
from routes import brand_kit, runs, approve

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PM Launch Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brand_kit.router)
app.include_router(runs.router)
app.include_router(approve.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
