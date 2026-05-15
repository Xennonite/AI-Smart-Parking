import cv2
import numpy as np
import requests
import json
import time
from ultralytics import YOLO

# ==========================================
# ⚙️ CONFIGURATION ZONE
# ==========================================
CAMERA_URL = "http://esp32cam.local/capture"
ESP_URL = "http://esp32.local/status" 

# ==========================================

print("Loading AI Brain...")
model = YOLO('best.pt')

print("Loading Parking Map...")
try:
    with open('parking_data.json', 'r') as f:
        slots = json.load(f)
except FileNotFoundError:
    print("Error: parking_data.json not found! Run Step 1 first.")
    exit()

cv2.namedWindow('Smart Parking Master', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Smart Parking Master', 1024, 768)

print("\n🚀 SPEED OPTIMIZED SYSTEM ONLINE! Press 'q' to quit.")

# Variables for calculating speed
prev_time = time.time()

while True:
    loop_start_time = time.time()

    # 1. FETCH THE IMAGE (Now much faster if you lowered the resolution to SVGA)
    try:
        response = requests.get(CAMERA_URL, timeout=2)
        img_array = np.array(bytearray(response.content), dtype=np.uint8)
        frame = cv2.imdecode(img_array, -1)
    except Exception as e:
        print("Waiting for camera connection...")
        time.sleep(0.5)
        continue

    if frame is None:
        continue

    # 2. RUN AI INFERENCE
    results = model(frame, verbose=False)
    car_centers = []
    
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            car_centers.append((cx, cy))
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

    # 3. CHECK THE SLOTS
    slot_array = [] 

    for i, pts in enumerate(slots):
        pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
        is_filled = 0
        
        for cx, cy in car_centers:
            if cv2.pointPolygonTest(pts_arr, (cx, cy), False) >= 0:
                is_filled = 1
                break
                
        slot_array.append(is_filled)
        
        color = (0, 0, 255) if is_filled == 1 else (0, 255, 0)
        cv2.polylines(frame, [pts_arr], True, color, 2)
        cv2.putText(frame, f"S{i+1}", (pts[0][0], pts[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # 4. SEND DATA TO LCD
    payload = {"slots": slot_array}
    
    try:
        requests.post(ESP_URL, json=payload, timeout=0.5)
    except Exception:
        pass # Ignore missed pings to keep the video running fast

    # 5. CALCULATE SPEED AND DISPLAY
    current_time = time.time()
    loop_time = current_time - prev_time
    fps = 1 / loop_time if loop_time > 0 else 0
    prev_time = current_time

    # Dashboard HUD
    cv2.putText(frame, f"Array Sent: {slot_array}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
    cv2.putText(frame, f"Array Sent: {slot_array}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Speed HUD (Green if fast, Red if slow)
    speed_color = (0, 255, 0) if loop_time < 1.0 else (0, 0, 255)
    cv2.putText(frame, f"Latency: {loop_time:.2f}s | FPS: {fps:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(frame, f"Latency: {loop_time:.2f}s | FPS: {fps:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, speed_color, 2)

    cv2.imshow('Smart Parking Master', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()