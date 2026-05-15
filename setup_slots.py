import cv2
import numpy as np
import requests
import json

url = "http://esp32cam.local/capture"

print("Fetching a high-res image from ESP32-CAM. Please wait...")

try:
    # Ask the ESP32 for ONE picture
    response = requests.get(url, timeout=5)
    
    # Convert the downloaded bytes into an OpenCV image
    img_array = np.array(bytearray(response.content), dtype=np.uint8)
    frame = cv2.imdecode(img_array, -1)
except Exception as e:
    print(f"Error connecting to camera: {e}")
    print("Fix: If esp32cam.local fails, find the IP address on your hotspot and use that instead.")
    exit()

if frame is None:
    print("Failed to decode image.")
    exit()

slots = []
current_slot = []
total_slots = 8 

def draw_polygon(event, x, y, flags, param):
    global current_slot, slots
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(slots) < total_slots:
            current_slot.append((x, y))
            
            if len(current_slot) == 4:
                slots.append(current_slot)
                print(f"✅ Slot {len(slots)} mapped!")
                current_slot = []
                
                if len(slots) == total_slots:
                    with open('parking_data.json', 'w') as f:
                        json.dump(slots, f)
                    print("\n🎉 All 8 slots mapped! Data saved to parking_data.json.")
                    print("Press 'q' to close the window.")

# Create a resizable window so it fits on your screen
cv2.namedWindow('Step 1: Map 8 Slots', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Step 1: Map 8 Slots', 1024, 768)
cv2.setMouseCallback('Step 1: Map 8 Slots', draw_polygon)

print("\n--- INSTRUCTIONS ---")
print("1. Click the 4 corners of each parking slot.")
print("2. Draw them in physical order (Slot 1 first, Slot 8 last).")

while True:
    # Draw on a copy so we don't ruin the original image
    display_frame = frame.copy()
    
    # Draw completed slots
    for i, slot in enumerate(slots):
        cv2.polylines(display_frame, [np.array(slot, np.int32)], True, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Slot {i+1}", (slot[0][0], slot[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw the slot currently being clicked
    if len(current_slot) > 0:
        for pt in current_slot:
            cv2.circle(display_frame, pt, 4, (0, 0, 255), -1)
        if len(current_slot) > 1:
            cv2.polylines(display_frame, [np.array(current_slot, np.int32)], False, (0, 0, 255), 1)

    cv2.putText(display_frame, f"Mapped: {len(slots)}/{total_slots}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow('Step 1: Map 8 Slots', display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()