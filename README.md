# Driver Drowsiness Demo

A prototype driver monitoring demo that detects drowsiness, fatigue, distraction, and micromoment events using webcam input.

The project uses MediaPipe FaceMesh for facial landmark detection and evaluates eye closure, yawning, head pose, and face presence to compute a real-time risk score.

## Features

- Webcam-based driver state monitoring
- Drowsiness detection using Eye Aspect Ratio (EAR)
- Yawn and fatigue detection
- Distraction detection when the face is not present or the driver looks away
- Real-time risk scoring and alert levels
- Local alarm cooldown control
- `ntfy.sh` push notifications for high-risk alerts
- Event logging to `events.log`
- Two demo entrypoints:
  - `main.py` - OpenCV local camera display
  - `ui_app.py` - Streamlit dashboard

## Requirements

- Python 3.11 or 3.12
- Webcam or compatible camera device

## Installation

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

If `pip install -e .` does not work for your environment, install the dependencies directly:

```powershell
python -m pip install mediapipe==0.10.21 numpy>=1.26.0,<2 opencv-python python-dotenv requests streamlit
```

## Configuration

This project reads settings from environment variables via `.env`. Create a `.env` file in the project root to override defaults.

Example `.env`:

```ini
CAMERA_INDEX=0
EAR_THRESHOLD=0.25
EYE_CLOSED_SECONDS=2.0
MICROSLEEP_SECONDS=0.7
FATIGUE_WINDOW_SECONDS=120
FATIGUE_MICROSLEEP_COUNT=3
MOUTH_OPEN_THRESHOLD=0.6
YAWN_SECONDS=1.5
FATIGUE_YAWN_COUNT=2
HEAD_YAW_RATIO_THRESHOLD=0.28
HEAD_DOWN_RATIO_THRESHOLD=-0.35
DISTRACTION_SECONDS=2.0
NO_FACE_SECONDS=2.0
ALARM_COOLDOWN_SECONDS=20
NTFY_TOPIC_URL=https://ntfy.sh/driver-FDD
```

Important settings:

- `CAMERA_INDEX`: camera device index for OpenCV
- `EAR_THRESHOLD`: threshold to consider eyes closed
- `EYE_CLOSED_SECONDS`: minimum closed-eye duration for drowsiness
- `NTFY_TOPIC_URL`: ntfy.sh topic URL used for alert notifications

## Running the Demo

### Local webcam demo

```powershell
python main.py
```

Press `q` to quit the OpenCV window.

### Streamlit dashboard

```powershell
streamlit run ui_app.py
```

Open the local Streamlit URL shown in the console.

## Project Structure

- `main.py` - OpenCV monitoring demo with on-screen dashboard and alerting
- `ui_app.py` - Streamlit web UI version of the same monitoring demo
- `config/settings.py` - configuration via `.env`
- `detectors/drowsiness_detector.py` - driver-state detection logic
- `detectors/eye_utils.py` - EAR calculations and landmark utilities
- `scoring/confidence_score.py` - risk score and risk-level mapping
- `alerts/alarm.py` - cooldown alarm control
- `alerts/ntfy_alert.py` - ntfy.sh alert sender
- `storage/event_logger.py` - event log writer

## Notes

- Alerts are rate-limited by `ALARM_COOLDOWN_SECONDS`.
- High-risk alerts are sent only when the system reaches `RISKY` or `CRITICAL` risk levels.
- Detected events are appended to `events.log` in the project root.

## Troubleshooting

- If the webcam does not open, try changing `CAMERA_INDEX` in `.env` from `0` to `1` or another index.
- If `ntfy` notifications fail, verify that `NTFY_TOPIC_URL` is valid and the network is available.
- Ensure your Python version is within the supported range.
