# Smart Road Damage Reporting and Management System

A modern, AI-powered system for reporting and managing road damage.

## 🚀 Features
- **Citizen Portal**: Upload photos, AI-based damage classification, and GPS extraction.
- **Municipality Dashboard**: Analytics, trends, and real-time complaint management.
- **AI Integration**: CNN-based detection (simulated) and EXIF GPS metadata extraction.
- **Modern UI**: Built with React, Tailwind CSS, Headless UI, and Framer Motion.

## 🛠 Tech Stack
- **Frontend**: React.js, Tailwind CSS, Lucide Icons, Recharts, Leaflet.
- **Backend**: FastAPI (Python), SQLAlchemy, SQLite.
- **AI**: TensorFlow/Keras (simulated), Pillow, ExifRead.

## 🏃 How to Run Locally

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
Backend will be available at `http://localhost:8000`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at `http://localhost:5173`.

## 📁 Project Structure
- `backend/`: FastAPI server, database models, and AI logic.
- `frontend/`: React components, pages, and styling.
- `ai_model/`: Storage for actual CNN model weights (if applicable).
