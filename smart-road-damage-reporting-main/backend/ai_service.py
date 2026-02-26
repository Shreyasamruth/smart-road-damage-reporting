from ultralytics import YOLO
import numpy as np
from PIL import Image
import exifread
import io
import os

# Path to the trained YOLOv8 model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_weights", "best.pt")

# Initialize model
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
else:
    # Use pre-trained base model if custom weights are not found
    model = YOLO('yolov8n-seg.pt')

def classify_road_damage(image_bytes):
    """
    Classifies the image for road damage using YOLOv8 Pothole Segmentation.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        if width < 100 or height < 100:
            return {
                "status": "error",
                "result": "Invalid Image - Resolution too low",
                "type": None,
                "confidence": 0.0
            }
        
        # Run inference
        results = model.predict(source=img, conf=0.25, verbose=False)
        
        if not results or len(results[0].boxes) == 0:
            return {
                "status": "success",
                "result": "No Road Damage",
                "type": None,
                "confidence": 0.0
            }
        
        # Get detections
        boxes = results[0].boxes
        # Get the one with highest confidence
        max_conf_idx = np.argmax(boxes.conf.cpu().numpy())
        confidence = float(boxes.conf[max_conf_idx])
        class_id = int(boxes.cls[max_conf_idx])
        label = results[0].names[class_id]
        
        # Get coordinates [x1, y1, x2, y2]
        coords = boxes.xyxy[max_conf_idx].cpu().numpy().tolist()
        
        return {
            "status": "success",
            "result": "Road Damage Detected",
            "type": label,
            "confidence": confidence,
            "bbox": coords
        }
        
    except Exception as e:
        print(f"AI Classification failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def extract_gps_data(image_bytes):
    """
    Extracts GPS coordinates from image EXIF data using Pillow.
    """
    try:
        from PIL.ExifTags import TAGS, GPSTAGS
        img = Image.open(io.BytesIO(image_bytes))
        exif_info = img._getexif()
        
        if not exif_info:
            print("No EXIF data found in image.")
            return None

        gps_info = {}
        for tag, value in exif_info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_info[sub_tag] = value[t]

        if not gps_info:
            print("No GPS info found in EXIF.")
            return None

        def _convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = _convert_to_degrees(gps_info['GPSLatitude'])
            if gps_info.get('GPSLatitudeRef', 'N') != 'N':
                lat = -lat

            lon = _convert_to_degrees(gps_info['GPSLongitude'])
            if gps_info.get('GPSLongitudeRef', 'E') != 'E':
                lon = -lon

            print(f"Extracted GPS: {lat}, {lon}")
            return {"latitude": lat, "longitude": lon}

    except Exception as e:
        print(f"GPS Extraction failed: {e}")
        
    return None
