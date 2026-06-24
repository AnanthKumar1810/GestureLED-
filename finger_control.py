import sys
import os

# ==========================================
# DEPENDENCY CHECK
# Catches missing modules early and tells you the exact pip command to run.
# ==========================================
_missing = []

try:
    import cv2
except ImportError:
    _missing.append(("cv2", "opencv-python"))

try:
    import mediapipe as mp
except ImportError:
    _missing.append(("mediapipe", "mediapipe"))

try:
    import serial
except ImportError:
    _missing.append(("serial", "pyserial"))

if _missing:
    print("\n❌ Missing required module(s):\n")
    for import_name, pip_name in _missing:
        print(f"   - '{import_name}' is not installed. Run: pip install {pip_name}")
    print("\nTip: if you already ran 'pip install serial', that installs the WRONG")
    print("package. Run 'pip uninstall serial' then 'pip install pyserial'.\n")
    sys.exit(1)

import math
import time
import urllib.request

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ==========================================
# CONFIGURATION
# ⚠️ UPDATE THIS PORT TO MATCH YOUR ESP32!
SERIAL_PORT = 'COM5'
BAUD_RATE = 9600
THRESHOLD = 60  # Distance threshold for pinch sensitivity
# ==========================================

# ------------------------------------------
# Download the hand landmark model if it isn't already on disk.
# (Newer mediapipe needs an explicit model file; the old mp.solutions API
# used to bundle this automatically — that's the part that changed.)
# ------------------------------------------
MODEL_PATH = 'hand_landmarker.task'
MODEL_URL = (
    'https://storage.googleapis.com/mediapipe-models/'
    'hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
)
if not os.path.exists(MODEL_PATH):
    print("Downloading hand landmark model (one-time, ~10 MB)...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")
    except Exception as e:
        print(f"❌ Could not download model automatically: {e}")
        print(f"Manually download it from:\n{MODEL_URL}")
        print(f"and place it next to this script as '{MODEL_PATH}'.")
        sys.exit(1)

# Initialize Serial Communication with ESP32
try:
    esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Give ESP32 bootloader time to initialize
    print(f"Successfully connected to ESP32 on {SERIAL_PORT}!")
except Exception as e:
    print(f"Connection Error: {e}")
    print("Running in simulation mode (Video only).")
    esp32 = None

# Initialize MediaPipe Hand Landmarker (new Tasks API)
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=mp_vision.RunningMode.VIDEO,
)
landmarker = mp_vision.HandLandmarker.create_from_options(options)

# Open Webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open webcam. Check that it's connected and not in use by another app.")
    sys.exit(1)

print("\n--- System Running ---")
print("Press 'q' in the video window to quit.")

start_time = time.time()

while cap.isOpened():
    success, img = cap.read()
    if not success:
        continue

    # Flip horizontally for a natural mirror view
    img = cv2.flip(img, 1)
    h, w, c = img.shape

    # Convert BGR to RGB for MediaPipe
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    # Timestamp must be increasing for VIDEO mode
    frame_timestamp_ms = int((time.time() - start_time) * 1000)
    result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

    if result.hand_landmarks:
        for hand_lms in result.hand_landmarks:
            # Draw a small dot for every landmark (simple skeleton view)
            for lm in hand_lms:
                cv2.circle(img, (int(lm.x * w), int(lm.y * h)), 3, (200, 200, 200), cv2.FILLED)

            # Get positions of Thumb tip (4) and Index tip (8)
            thumb = hand_lms[4]
            index = hand_lms[8]

            # Convert normalized coordinates to pixels
            x1, y1 = int(thumb.x * w), int(thumb.y * h)
            x2, y2 = int(index.x * w), int(index.y * h)

            # Draw circles on fingertips
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 0), 2)

            # Calculate the Euclidean distance between fingertips
            distance = math.hypot(x2 - x1, y2 - y1)

            # Check threshold and set command
            if distance < THRESHOLD:
                command = '1'
                display_text = f"LED: ON (Dist: {int(distance)})"
                text_color = (0, 255, 0)
            else:
                command = '0'
                display_text = f"LED: OFF (Dist: {int(distance)})"
                text_color = (0, 0, 255)

            # Send data to ESP32
            if esp32:
                esp32.write(command.encode())

            # Show status on screen
            cv2.putText(img, display_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

    cv2.imshow("Finger Control Hub", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
if esp32:
    esp32.close()