from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime
from typing import List

import models, ai_service, database
from database import engine, SessionLocal

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for uploads - use /tmp on Vercel
IS_VERCEL = os.environ.get("VERCEL") == "1"
UPLOAD_DIR = "/tmp/uploads" if IS_VERCEL else "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "environment": "vercel" if IS_VERCEL else "local"}

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/validate-image")
async def validate_image(file: UploadFile = File(...)):
    contents = await file.read()
    
    # AI Classification
    ai_result = ai_service.classify_road_damage(contents)
    
    # GPS Extraction
    gps_data = ai_service.extract_gps_data(contents)
    
    return {
        "ai_result": ai_result,
        "gps_data": gps_data
    }

@app.post("/api/report")
async def create_complaint(
    name: str = Form(...),
    phone: str = Form(...),
    ward: str = Form(...),
    damage_type: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        complaint_id = str(uuid.uuid4())[:8].upper()
        file_path = os.path.join(UPLOAD_DIR, f"{complaint_id}_{image.filename}")
        
        contents = await image.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Run AI inference
        import json
        ai_result = ai_service.classify_road_damage(contents)
        confidence = ai_result.get("confidence", 0.0)
        metadata = json.dumps(ai_result.get("bbox", []))
        
        db_complaint = models.Complaint(
            complaint_id=complaint_id,
            citizen_name=name,
            phone=phone,
            ward=ward,
            damage_type=damage_type,
            description=description,
            image_path=file_path,
            latitude=latitude,
            longitude=longitude,
            ai_confidence=confidence,
            ai_metadata=metadata,
            status="Pending",
            created_at=datetime.utcnow()
        )
        
        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)
        
        return {"message": "Complaint Registered Successfully", "complaint_id": complaint_id}
    except Exception as e:
        print(f"❌ Error creating complaint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/complaints", response_model=List[dict])
async def get_complaints(db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).all()
    return [
        {
            "complaint_id": c.complaint_id,
            "citizen_name": c.citizen_name,
            "ward": c.ward,
            "damage_type": c.damage_type,
            "status": c.status,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "created_at": c.created_at,
            "image_path": c.image_path,
            "ai_confidence": c.ai_confidence,
            "ai_metadata": c.ai_metadata
        } for c in complaints
    ]

@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    total = db.query(models.Complaint).count()
    pending = db.query(models.Complaint).filter(models.Complaint.status == "Pending").count()
    in_progress = db.query(models.Complaint).filter(models.Complaint.status == "In Progress").count()
    resolved = db.query(models.Complaint).filter(models.Complaint.status == "Resolved").count()
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved
    }

@app.patch("/api/complaints/{complaint_id}")
async def update_complaint(
    complaint_id: str,
    status: str = Form(...),
    remarks: str = Form(None),
    db: Session = Depends(get_db)
):
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = status
    if remarks:
        complaint.remarks = remarks
    if status == "Resolved":
        complaint.resolved_at = datetime.utcnow()
        
    db.commit()
    return {"message": "Status updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
