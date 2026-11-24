import os
from ultralytics import YOLO

def download_fallback():
    print("--- StockSnap AI Setup (Pivoting to YOLOv8) ---")
    
    # YOLOv8n is the most stable and widely supported model
    model_name = "yolov8n.pt" 
    
    try:
        print(f"Requesting {model_name} from Ultralytics...")
        # This will download the file to your backend/ folder automatically
        model = YOLO(model_name) 
        
        print(f"✅ Success! {model_name} saved to: {os.path.abspath(model_name)}")
        print(f"Ready to detect {len(model.names)} retail-relevant classes.")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    download_fallback()