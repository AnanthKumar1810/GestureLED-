<p align="center">
  <img src="banner.svg" alt="Finger Pinch LED Controller banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<p align="center">
  Pinch your thumb and index finger together in front of a webcam to turn a real LED on or off — hand tracking via MediaPipe, hardware control via ESP32 over serial.
</p>

## Demo

> _Add a screenshot or short GIF here showing the pinch gesture toggling the LED — this is the first thing visitors will look at._

## Instructions

### 1. Requirements

**Hardware**
- A webcam
- An ESP32 board
- An LED (+ resistor) wired to a GPIO pin on the ESP32
- A USB cable connecting the ESP32 to your computer

**Software**
- Python 3.9–3.12 (MediaPipe doesn't currently ship pre-built wheels for newer versions — see [Troubleshooting](#troubleshooting))
- [Arduino IDE](https://www.arduino.cc/en/software) (to flash the ESP32)

### 2. Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Flash the ESP32

Upload a sketch that listens on serial and toggles an LED based on the byte it receives:

```cpp
#define LED_PIN 2  // change to whichever GPIO your LED is wired to

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      digitalWrite(LED_PIN, HIGH);
    } else if (command == '0') {
      digitalWrite(LED_PIN, LOW);
    }
  }
}
```

Find your ESP32's serial port:
- **Windows:** Device Manager → Ports (COM & LPT), e.g. `COM5`
- **macOS:** `ls /dev/tty.*`
- **Linux:** `ls /dev/ttyUSB*`

### 4. Configure

Open `finger_control_hub.py` and set:

| Variable | Description | Default |
|---|---|---|
| `SERIAL_PORT` | Serial port the ESP32 is connected on | `'COM5'` |
| `BAUD_RATE` | Must match `Serial.begin()` in the Arduino sketch | `9600` |
| `THRESHOLD` | Pixel distance below which fingers count as "pinched" | `60` |

`THRESHOLD` is a pixel distance, not a real-world unit — it depends on your webcam's resolution and how far your hand is from the camera. The on-screen text shows the live distance value (`Dist: NN`) so you can tune it while pinching/releasing.

### 5. Run

```bash
python finger_control_hub.py
```

On first run, the script downloads MediaPipe's hand landmark model (`hand_landmarker.task`, ~10 MB) into the project folder — this only happens once.

If the ESP32 isn't connected or the port is wrong, the script still runs in **simulation mode**: you'll see the video feed and gesture detection, but no serial data is sent.

Press **`q`** in the video window to quit.

## Closing

### Additional notes

**Project structure**
```
.
├── finger_control_hub.py     # main script
├── requirements.txt          # Python dependencies
├── banner.svg                # README banner
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
└── hand_landmarker.task      # auto-downloaded on first run (gitignored)
```

**Troubleshooting**

<details>
<summary><code>ModuleNotFoundError: No module named 'cv2' / 'mediapipe' / 'serial'</code></summary>

Install the missing package. Note the package name doesn't always match the import name:

| Import | Install with |
|---|---|
| `cv2` | `pip install opencv-python` |
| `mediapipe` | `pip install mediapipe` |
| `serial` | `pip install pyserial` (**not** `pip install serial`) |

</details>

<details>
<summary><code>AttributeError: module 'mediapipe' has no attribute 'solutions'</code></summary>

MediaPipe removed the legacy `mp.solutions` API starting in version `0.10.30`. This script already uses the replacement `HandLandmarker` Tasks API, so you shouldn't hit this running the script as-is.

</details>

<details>
<summary><code>ERROR: No matching distribution found for mediapipe==X.X.X</code></summary>

MediaPipe doesn't publish wheels for every Python version. If you're on a very new Python release (e.g. 3.13+), use Python 3.10–3.12 in your virtual environment instead.

</details>

<details>
<summary>Webcam won't open</summary>

Check it isn't already in use by another application (Zoom, Teams, a browser tab, etc.), and that you've granted camera permission to your terminal/IDE.

</details>

<details>
<summary>LED doesn't respond but the video feed works fine</summary>

- Confirm `SERIAL_PORT` matches the port shown in Device Manager / `ls /dev/tty*`.
- Confirm `BAUD_RATE` matches `Serial.begin()` in the Arduino sketch.
- Close any other program (including the Arduino IDE's Serial Monitor) that might be holding the port open — only one program can use a serial port at a time.

</details>

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues and submitting pull requests.

### License

This project is licensed under the [MIT License](LICENSE).

### Support

If this project was useful to you, consider starring ⭐ the repo — it helps others find it.

<p align="left">
  <a href="https://www.buymeacoffee.com/<your-username>"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black" alt="Buy me a coffee"></a>
</p>
