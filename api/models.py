from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String, primary_key=True, index=True)
    citizen_name = Column(String)
    phone = Column(String)
    ward = Column(String)
    damage_type = Column(String)
    description = Column(Text)
    image_path = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    ai_confidence = Column(Float, nullable=True)
    ai_metadata = Column(Text, nullable=True)
    status = Column(String, default="Pending") # Pending, In Progress, Resolved
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # admin, official
