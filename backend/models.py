from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base

class BrandKit(Base):
    __tablename__ = "brand_kits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    voice_tone = Column(Text, default="")
    do_list = Column(JSON, default=list)
    dont_list = Column(JSON, default=list)
    style_rules = Column(Text, default="")
    colors = Column(JSON, default=dict)
    typography = Column(JSON, default=dict)
    logo_url = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    brand_kit_id = Column(Integer, ForeignKey("brand_kits.id"), nullable=False)
    input_type = Column(String, nullable=False)  # paste | file
    raw_input = Column(Text, default="")
    filename = Column(String, nullable=True)
    status = Column(String, default="processing")  # processing | review | approved | rejected
    progress = Column(JSON, default=dict)  # {"orchestrator": "pending|running|done", ...}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class StructuredBrief(Base):
    __tablename__ = "structured_briefs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    product_name = Column(String, nullable=True)
    launch_date = Column(String, nullable=True)
    key_features = Column(JSON, default=list)
    target_audience = Column(Text, default="")
    launch_goals = Column(Text, default="")
    tone_notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Output(Base):
    __tablename__ = "outputs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    output_type = Column(String, nullable=False)  # marketing_copy | asset_specs
    content = Column(JSON, default=dict)
    status = Column(String, default="draft")  # draft | approved | rejected
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
