# Finger Pinch LED Controller

A webcam-based gesture controller that lets you turn a physical LED on or off by pinching your thumb and index finger together. Hand tracking is done on the computer with MediaPipe; the resulting on/off signal is sent to an ESP32 over USB serial, which drives the LED.

## How it works

```
Webcam frame
   │
   ▼
OpenCV reads + flips + color-converts the frame
   │
   ▼
MediaPipe HandLandmarker detects 21 hand landmarks
   │
   ▼
Script reads landmark 4 (thumb tip) and landmark 8 (index tip)
   │
   ▼
Euclidean distance between the two points is calculated
   │
   ▼
distance < THRESHOLD ?
   ├── yes → send '1' over serial → ESP32 sets LED pin HIGH
   └── no  → send '0' over serial → ESP32 sets LED pin LOW
```

Step by step:

1. **Capture** — OpenCV grabs a frame from the webcam and flips it horizontally so it behaves like a mirror.
2. **Detect** — The frame is converted to RGB and passed into MediaPipe's `HandLandmarker`, which returns 21 (x, y, z) points per detected hand. Coordinates come back normalized between 0 and 1, so the script multiplies by the frame's width/height to get actual pixel positions.
3. **Measure** — Only two of the 21 points matter for this gesture: landmark `4` (thumb tip) and landmark `8` (index fingertip). `math.hypot()` computes the straight-line pixel distance between them.
4. **Decide** — That distance is compared against `THRESHOLD`. Below it, the fingers are "pinched"; above it, they're "open."
5. **Send** — A single byte (`'1'` or `'0'`) is written to the serial port.
6. **Act** — The ESP32's firmware reads that byte and sets a GPIO pin HIGH or LOW, turning the LED on or off.

## Hardware components

| Component | Purpose |
|---|---|
| Webcam | Captures the video frames used for hand tracking |
| ESP32 board | Receives the serial command and drives the GPIO pin |
| LED + resistor | The actual output being switched |
| USB cable | Carries serial data between the computer and the ESP32 |

## Software components

| Component | Role |
|---|---|
| `OpenCV` (`cv2`) | Reads webcam frames, draws the on-screen overlay, handles color conversion |
| `MediaPipe` (`HandLandmarker`) | Machine learning model that detects hand landmarks per frame |
| `pyserial` (`serial`) | Sends bytes from Python to the ESP32 over USB |
| `hand_landmarker.task` | The trained model file MediaPipe uses; downloaded automatically on first run |
| ESP32 firmware (Arduino sketch) | Listens on serial and toggles a GPIO pin based on the byte received |

## Project structure

```
.
├── finger_control_hub.py     # main script — capture, detect, decide, send
├── requirements.txt          # opencv-python, mediapipe, pyserial
├── LICENSE
├── .gitignore
└── hand_landmarker.task      # auto-downloaded model file (not committed)
```

## Code walkthrough

`finger_control_hub.py` is organized into these sections, in order:

**1. Dependency check** — imports `cv2`, `mediapipe`, and `serial` inside `try/except` blocks. If any are missing, it prints the exact `pip install` command needed and exits, instead of crashing with a raw traceback.

**2. Model download** — checks whether `hand_landmarker.task` already exists locally. If not, downloads it once from Google's servers. This file is required by MediaPipe's Tasks API and isn't bundled with the package itself.

**3. Serial connection** — opens `SERIAL_PORT` at `BAUD_RATE`. If the ESP32 isn't connected or the port is wrong, `esp32` is set to `None` and the script keeps running in simulation mode (video + detection, no hardware output).

**4. HandLandmarker setup** — creates the detector with:
- `num_hands=1` — only track one hand
- `running_mode=VIDEO` — tells MediaPipe to expect a sequence of timestamped frames (enables frame-to-frame tracking instead of full re-detection every time)
- `min_hand_detection_confidence`, `min_hand_presence_confidence`, `min_tracking_confidence` — confidence thresholds (0–1) controlling how certain the model must be before accepting a detection

**5. Main loop** — runs once per frame:
- reads and flips the frame
- wraps it in an `mp.Image` and calls `landmarker.detect_for_video()` with an increasing timestamp
- if a hand is found, extracts landmarks 4 and 8, computes the distance, compares to `THRESHOLD`, writes `'1'`/`'0'` to serial, and draws the tracked points, the distance line, and the current state as text on the frame
- displays the frame and exits the loop when `q` is pressed

**6. Cleanup** — releases the webcam, closes the OpenCV window, closes the MediaPipe landmarker, and closes the serial connection if it was open.

## Setup

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Flash the ESP32 with a sketch that listens on serial and toggles a pin:

```cpp
#define LED_PIN 2

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') digitalWrite(LED_PIN, HIGH);
    else if (command == '0') digitalWrite(LED_PIN, LOW);
  }
}
```

Find the ESP32's serial port (Windows: Device Manager → Ports; macOS: `ls /dev/tty.*`; Linux: `ls /dev/ttyUSB*`) and set it in `finger_control_hub.py`.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `SERIAL_PORT` | Serial port the ESP32 is connected on | `'COM5'` |
| `BAUD_RATE` | Must match `Serial.begin()` in the Arduino sketch | `9600` |
| `THRESHOLD` | Pixel distance below which fingers count as "pinched" | `60` |

`THRESHOLD` is a pixel distance, not a physical unit — it depends on webcam resolution and distance from the camera. The on-screen `Dist: NN` readout shows the live value so you can tune it.

## Usage

```bash
python finger_control_hub.py
```

Press `q` in the video window to quit.

## Troubleshooting

- **`ModuleNotFoundError`** — install the missing package: `opencv-python` for `cv2`, `mediapipe` for `mediapipe`, `pyserial` for `serial` (not `serial`, which is a different package).
- **`AttributeError: module 'mediapipe' has no attribute 'solutions'`** — only relevant if you're adapting older MediaPipe code; this script already uses the current `HandLandmarker` API.
- **No matching mediapipe version for your Python** — MediaPipe doesn't publish wheels for every Python release. Use Python 3.10–3.12 in a virtual environment.
- **Webcam won't open** — check it isn't in use by another app, and that camera permission is granted to your terminal/IDE.
- **LED doesn't respond** — verify `SERIAL_PORT` and `BAUD_RATE` match the ESP32, and that no other program (e.g. the Arduino IDE's Serial Monitor) is holding the port open.

## License

MIT — see [LICENSE](LICENSE).
