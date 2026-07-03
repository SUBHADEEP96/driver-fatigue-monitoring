import time
from datetime import datetime

import cv2
import streamlit as st

from alerts.alarm import AlarmController
from alerts.whatsapp_alert import send_whatsapp_alert
from config.settings import settings
from detectors.drowsiness_detector import DrowsinessDetector
from scoring.confidence_score import calculate_confidence_score, get_risk_level
from storage.event_logger import log_event


def build_alert_message(detection_result: dict, score: int, risk_level: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        "🚨 Driver Alert!\n\n"
        f"Time: {timestamp}\n"
        f"Status: {detection_result['status']}\n"
        f"Risk Score: {score}/100\n"
        f"Risk Level: {risk_level}\n"
        f"Eyes Closed Duration: {detection_result['closed_duration']:.1f}s\n"
        f"Yawn Duration: {detection_result.get('yawn_duration', 0.0):.1f}s\n"
        f"Distraction Duration: {detection_result.get('distraction_duration', 0.0):.1f}s\n\n"
        "Action Required: Please check with the driver immediately."
    )


def get_risk_color_hex(risk_level: str) -> str:
    if risk_level == "SAFE":
        return "#16a34a"

    if risk_level == "WARNING":
        return "#ca8a04"

    if risk_level == "RISKY":
        return "#ea580c"

    return "#dc2626"


def draw_overlay(frame, detection_result: dict, score: int, risk_level: str):
    status = detection_result["status"]
    avg_ear = detection_result["avg_ear"]
    closed_duration = detection_result["closed_duration"]
    yawn_duration = detection_result.get("yawn_duration", 0.0)
    distraction_duration = detection_result.get("distraction_duration", 0.0)
    fatigue_events = detection_result.get("fatigue_events", 0)
    face_detected = detection_result["face_detected"]

    if risk_level == "SAFE":
        color = (0, 255, 0)
    elif risk_level == "WARNING":
        color = (0, 255, 255)
    elif risk_level == "RISKY":
        color = (0, 165, 255)
    else:
        color = (0, 0, 255)

    cv2.rectangle(frame, (10, 10), (720, 250), (0, 0, 0), -1)

    cv2.putText(
        frame,
        "Driver Monitoring Prototype",
        (25, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Face Detected: {face_detected}",
        (25, 78),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Driver Status: {status}",
        (25, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"Risk Score: {score}/100",
        (25, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"Risk Level: {risk_level}",
        (25, 185),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"EAR: {avg_ear:.3f} | Eyes Closed: {closed_duration:.1f}s",
        (25, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Yawn: {yawn_duration:.1f}s | Distraction: {distraction_duration:.1f}s | Fatigue Events: {fatigue_events}",
        (25, 235),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )

    return frame


def initialize_session_state():
    if "camera_running" not in st.session_state:
        st.session_state.camera_running = False

    if "last_status" not in st.session_state:
        st.session_state.last_status = "NOT_STARTED"

    if "last_score" not in st.session_state:
        st.session_state.last_score = 0

    if "last_risk_level" not in st.session_state:
        st.session_state.last_risk_level = "SAFE"

    if "last_alert_time" not in st.session_state:
        st.session_state.last_alert_time = "No alert yet"

    if "alert_count" not in st.session_state:
        st.session_state.alert_count = 0


def start_camera():
    st.session_state.camera_running = True


def stop_camera():
    st.session_state.camera_running = False


def main():
    st.set_page_config(
        page_title="Driver Monitoring Demo",
        page_icon="🚗",
        layout="wide",
    )

    initialize_session_state()

    st.title("🚗 Driver Monitoring Prototype")
    st.caption(
        "Webcam-based fatigue, drowsiness, and distraction detection demo with risk scoring, alarm, and optional WhatsApp alert."
    )

    with st.sidebar:
        st.header("Demo Controls")

        col_start, col_stop = st.columns(2)

        with col_start:
            st.button("▶️ Start Camera", type="primary", on_click=start_camera)

        with col_stop:
            st.button("⏹ Stop Camera", on_click=stop_camera)

        st.divider()

        st.subheader("Current Config")
        st.write(f"Camera Index: `{settings.CAMERA_INDEX}`")
        st.write(f"EAR Threshold: `{settings.EAR_THRESHOLD}`")
        st.write(f"Eye Closed Seconds: `{settings.EYE_CLOSED_SECONDS}`")
        st.write(f"Alarm Cooldown: `{settings.ALARM_COOLDOWN_SECONDS}` sec")
        st.write(f"WhatsApp Enabled: `{settings.ENABLE_WHATSAPP}`")

        st.divider()

        st.subheader("How to Demo")
        st.markdown(
            """
            1. Click **Start Camera**
            2. Face forward with eyes open → status should be **SAFE**
            3. Close eyes for 2+ seconds → **DROWSY**
            4. Yawn repeatedly or blink long → **FATIGUED**
            5. Look away or leave frame → **DISTRACTED**
            """
        )

    status_color = get_risk_color_hex(st.session_state.last_risk_level)

    metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)

    metric_col_1.metric("Driver Status", st.session_state.last_status)
    metric_col_2.metric("Risk Score", f"{st.session_state.last_score}/100")
    metric_col_3.metric("Risk Level", st.session_state.last_risk_level)
    metric_col_4.metric("Alerts Triggered", st.session_state.alert_count)

    st.markdown(
        f"""
        <div style="
            padding: 12px;
            border-radius: 10px;
            background-color: {status_color};
            color: white;
            font-weight: 700;
            margin-bottom: 16px;">
            Current System State: {st.session_state.last_risk_level}
        </div>
        """,
        unsafe_allow_html=True,
    )

    video_placeholder = st.empty()
    event_placeholder = st.empty()

    if not st.session_state.camera_running:
        st.info("Click **Start Camera** from the sidebar to begin live driver monitoring.")
        return

    detector = DrowsinessDetector()
    alarm_controller = AlarmController(
        cooldown_seconds=settings.ALARM_COOLDOWN_SECONDS
    )

    cap = cv2.VideoCapture(settings.CAMERA_INDEX)

    if not cap.isOpened():
        st.error("Could not open webcam. Try changing CAMERA_INDEX in your .env file from 0 to 1.")
        st.session_state.camera_running = False
        return

    event_placeholder.success("Camera started. Monitoring driver state...")

    while st.session_state.camera_running:
        success, frame = cap.read()

        if not success:
            event_placeholder.error("Failed to read frame from webcam.")
            break

        frame = cv2.flip(frame, 1)

        detection_result = detector.process_frame(frame)
        score = calculate_confidence_score(detection_result)
        risk_level = get_risk_level(score)

        st.session_state.last_status = detection_result["status"]
        st.session_state.last_score = score
        st.session_state.last_risk_level = risk_level

        should_alert = risk_level in ["RISKY", "CRITICAL"]

        if should_alert:
            alarm_started = alarm_controller.trigger_alarm()

            if alarm_started:
                alert_message = build_alert_message(
                    detection_result=detection_result,
                    score=score,
                    risk_level=risk_level,
                )

                send_whatsapp_alert(alert_message)

                log_event(
                    status=detection_result["status"],
                    score=score,
                    risk_level=risk_level,
                    avg_ear=detection_result["avg_ear"],
                    closed_duration=detection_result["closed_duration"],
                    yawn_duration=detection_result.get("yawn_duration", 0.0),
                    distraction_duration=detection_result.get("distraction_duration", 0.0),
                    fatigue_events=detection_result.get("fatigue_events", 0),
                )

                st.session_state.alert_count += 1
                st.session_state.last_alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                event_placeholder.warning(
                    f"Alert triggered at {st.session_state.last_alert_time}: {risk_level}"
                )

        output_frame = draw_overlay(frame, detection_result, score, risk_level)

        output_frame_rgb = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)

        video_placeholder.image(
            output_frame_rgb,
            channels="RGB",
            use_container_width=True,
        )

        time.sleep(0.03)

    cap.release()
    event_placeholder.info("Camera stopped.")


if __name__ == "__main__":
    main()