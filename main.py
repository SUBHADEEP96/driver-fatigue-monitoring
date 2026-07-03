import cv2
from datetime import datetime

from alerts.alarm import AlarmController
from alerts.whatsapp_alert import send_whatsapp_alert
from config.settings import settings
from detectors.drowsiness_detector import DrowsinessDetector
from scoring.confidence_score import calculate_confidence_score, get_risk_level
from storage.event_logger import log_event


def get_risk_color(risk_level: str) -> tuple[int, int, int]:
    """
    OpenCV uses BGR colors, not RGB.
    """

    if risk_level == "SAFE":
        return 0, 255, 0

    if risk_level == "WARNING":
        return 0, 255, 255

    if risk_level == "RISKY":
        return 0, 165, 255

    return 0, 0, 255


def draw_dashboard(frame, detection_result: dict, score: int, risk_level: str):
    """
    Draws a simple dashboard overlay on the camera feed.
    """

    status = detection_result["status"]
    avg_ear = detection_result["avg_ear"]
    closed_duration = detection_result["closed_duration"]
    yawn_duration = detection_result.get("yawn_duration", 0.0)
    distraction_duration = detection_result.get("distraction_duration", 0.0)
    fatigue_events = detection_result.get("fatigue_events", 0)
    face_detected = detection_result["face_detected"]

    color = get_risk_color(risk_level)

    cv2.rectangle(frame, (10, 10), (690, 245), (0, 0, 0), -1)

    cv2.putText(
        frame,
        "Driver Monitoring Prototype",
        (25, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Face Detected: {face_detected}",
        (25, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Driver Status: {status}",
        (25, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"Risk Score: {score}/100",
        (25, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"Risk Level: {risk_level}",
        (25, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )

    cv2.putText(
        frame,
        f"EAR: {avg_ear:.3f} | Eyes Closed: {closed_duration:.1f}s",
        (25, 205),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
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


def build_alert_message(detection_result: dict, score: int, risk_level: str) -> str:
    """
    Builds owner alert message.
    """

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


def main():
    detector = DrowsinessDetector()

    alarm_controller = AlarmController(
        cooldown_seconds=settings.ALARM_COOLDOWN_SECONDS
    )

    cap = cv2.VideoCapture(settings.CAMERA_INDEX)

    if not cap.isOpened():
        print("Could not open webcam.")
        print("Try changing CAMERA_INDEX in .env from 0 to 1.")
        return

    print("Driver Monitoring Prototype Started")
    print("Press 'q' to quit")
    print(f"WhatsApp enabled: {settings.ENABLE_WHATSAPP}")

    while True:
        success, frame = cap.read()

        if not success:
            print("Failed to read frame from webcam.")
            break

        # Mirror effect for laptop demo.
        frame = cv2.flip(frame, 1)

        detection_result = detector.process_frame(frame)
        score = calculate_confidence_score(detection_result)
        risk_level = get_risk_level(score)

        draw_dashboard(frame, detection_result, score, risk_level)

        should_alert = risk_level in ["RISKY", "CRITICAL"]

        if should_alert:
            alarm_started = alarm_controller.trigger_alarm()

            # Only log/send notification when a fresh alarm starts.
            # This avoids WhatsApp spam every frame.
            if alarm_started:
                alert_message = build_alert_message(
                    detection_result=detection_result,
                    score=score,
                    risk_level=risk_level,
                )

                print(alert_message)

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

        cv2.imshow("Driver Monitoring Prototype", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Driver Monitoring Prototype Stopped")


if __name__ == "__main__":
    main()