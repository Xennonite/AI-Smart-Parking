import cv2
import numpy as np
import requests
import os

# Create folder for your training images
output_dir = "raw_images_high_res"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

url = "http://esp32cam.local/capture"

print("\n--- HIGH-RES PHOTOSHOOT ---")
print("Move your cars. Press 'c' on your keyboard to take a high-quality picture.")
print("Press 'q' to quit.")

img_count = 0

# Create a resizable window
cv2.namedWindow('Camera View', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Camera View', 800, 600)

while True:
    try:
        # 1. Ask the ESP32 for ONE picture
        response = requests.get(url, timeout=3)
        
        # 2. Convert the downloaded bytes into an OpenCV image
        img_array = np.array(bytearray(response.content), dtype=np.uint8)
        frame = cv2.imdecode(img_array, -1)
        
        if frame is None:
            continue

        # Show the live feed (updating as fast as the Wi-Fi allows)
        cv2.imshow('Camera View', frame)

        key = cv2.waitKey(100) & 0xFF
        
        if key == ord('c'):
            # Save the image
            img_name = f"{output_dir}/car_frame_{img_count}.jpg"
            cv2.imwrite(img_name, frame)
            print(f"✅ Captured High-Res Image: {img_count}")
            img_count += 1
            
        elif key == ord('q'):
            break

    except Exception as e:
        print(f"Waiting for camera... (Error: {e})")
        cv2.waitKey(1000) # Wait a second before trying again

cv2.destroyAllWindows()