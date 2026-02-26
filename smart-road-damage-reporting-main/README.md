# 🛣️ RoadWise AI: Smart Road Damage Reporting System

![RoadWise AI Banner](./assets/banner.png)

## 🌟 Overview
**RoadWise AI** is a state-of-the-art, AI-powered platform designed to revolutionize how road damage is reported, tracked, and repaired. By leveraging computer vision (YOLOv8) and real-time geolocation mapping, it bridges the gap between citizens and municipal authorities, ensuring safer roads through technology.

---

## 🚀 Key Features

### 👤 Citizen Portal
- **Instant Reporting**: Upload photos of potholes or road cracks directly from your device.
- **AI Damage Detection**: Integrated YOLOv8 model automatically identifies and validates the type of damage.
- **Smart Geolocation**: Automatically extracts GPS coordinates (latitude/longitude) from image EXIF metadata for precise mapping.
- **Track Progress**: Real-time status updates on submitted complaints.

### 🏛️ Municipality Dashboard
- **Comprehensive Analytics**: Visualize damage distribution across different wards using interactive charts.
- **Complaint Management**: View, assign, and update the status of repairs (Pending ➡️ In Progress ➡️ Resolved).
- **Interactive Mapping**: Leaflet-based map view showing exactly where the issues are located.
- **Performance Tracking**: Insights into resolution times and total complaints handled.

### 🧠 Advanced AI Integration
- **YOLOv8 Segmentation**: High-accuracy pothole and crack detection using custom-trained weights.
- **Automated Validation**: Prevents fake or irrelevant report submissions by analyzing image content.
- **GPS Extraction**: Intelligent parsing of image metadata to automate location tagging.

---

## 🛠 Tech Stack

### Frontend
- **Framework**: [React.js](https://reactjs.org/) (Vite)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Charts**: [Recharts](https://recharts.org/)
- **Maps**: [Leaflet](https://leafletjs.com/) & [React-Leaflet](https://react-leaflet.js.org/)
- **Icons**: [Lucide React](https://lucide.dev/)

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) with SQLite
- **AI/ML**: [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- **Auth**: JWT (JSON Web Tokens) with Passlib (Bcrypt)

---

## 🏃 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

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
*Backend will be running at `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend will be running at `http://localhost:5173`*

---

## 📂 Project Structure

```text
smart-road-damage-reporting/
├── backend/                # FastAPI server & AI logic
│   ├── ai_service.py       # YOLOv8 inference & GPS extraction
│   ├── main.py             # API endpoints
│   ├── models.py           # Database schemas
│   └── uploads/            # Stored complaint images
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # UI Components
│   │   ├── pages/          # Dashboard & Citizen views
│   │   └── utils/          # API helpers
├── assets/                 # Documentation assets (banners, icons)
└── README.md
```

---

## 🎯 Implementation Roadmap
- [x] YOLOv8 Model Integration
- [x] Real-time GPS Metadata Extraction
- [x] Multi-file upload support
- [ ] Push Notifications for repair updates
- [ ] Mobile App (Flutter/React Native)
- [ ] Automated Repair Cost Estimation

---

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.

---
*Developed with ❤️ for safer roads.*
