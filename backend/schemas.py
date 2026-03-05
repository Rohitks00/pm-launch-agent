from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# --- Brand Kit ---

class BrandKitCreate(BaseModel):
    name: str
    voice_tone: str = ""
    do_list: List[str] = []
    dont_list: List[str] = []
    style_rules: str = ""
    colors: dict = {}
    typography: dict = {}
    logo_url: str = ""

class BrandKitOut(BrandKitCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Runs ---

class RunCreatePaste(BaseModel):
    brand_kit_id: int
    raw_input: str

class RunOut(BaseModel):
    id: int
    brand_kit_id: int
    input_type: str
    raw_input: str
    filename: Optional[str]
    status: str
    progress: dict
    created_at: datetime
    class Config:
        from_attributes = True

# --- Structured Brief ---

class StructuredBriefOut(BaseModel):
    id: int
    run_id: int
    product_name: Optional[str]
    launch_date: Optional[str]
    key_features: List[dict]
    target_audience: str
    launch_goals: str
    tone_notes: str
    class Config:
        from_attributes = True

class StructuredBriefUpdate(BaseModel):
    product_name: Optional[str] = None
    launch_date: Optional[str] = None
    key_features: Optional[List[dict]] = None
    target_audience: Optional[str] = None
    launch_goals: Optional[str] = None
    tone_notes: Optional[str] = None

# --- Outputs ---

class OutputOut(BaseModel):
    id: int
    run_id: int
    output_type: str
    content: Any
    status: str
    feedback: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class ApproveRequest(BaseModel):
    status: str  # approved | rejected
    feedback: Optional[str] = None
