import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("smart-road-damage-reporting-main/backend"))

import ai_service
from PIL import Image
import io

def test_inference():
    # Path to a sample pothole image
    sample_image_path = r"C:\Users\PUNITH ARADHYA P\OneDrive\Desktop\roads\Pothole_Segmentation_YOLOv8\valid\images\pic-308-_jpg.rf.8f5b6dc0b616365d05bce17bf30eff39.jpg"
    
    if not os.path.exists(sample_image_path):
        print(f"❌ Sample image not found at {sample_image_path}")
        return

    print(f"🔍 Loading sample image: {os.path.basename(sample_image_path)}")
    
    with open(sample_image_path, "rb") as f:
        image_bytes = f.read()

    print("🚀 Running AI Inference...")
    result = ai_service.classify_road_damage(image_bytes)

    print("\n📊 INFERENCE RESULT:")
    print("-------------------")
    for key, value in result.items():
        print(f"{key}: {value}")
    print("-------------------")

    if result.get("result") == "Road Damage Detected":
        print("✅ SUCCESS: Road damage correctly detected!")
    else:
        print("⚠️ WARNING: Detection result unexpected. Check model confidence or image content.")

if __name__ == "__main__":
    test_inference()
