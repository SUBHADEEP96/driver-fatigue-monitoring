def calculate_confidence_score(detection_result: dict) -> int:
    """Convert driver-state signals into a 0-100 operational risk score."""
    score = 0

    if not detection_result.get("face_detected", False):
        score += 35
        score += int(min(35, float(detection_result.get("distraction_duration", 0.0)) * 12))
        return max(0, min(100, score))

    avg_ear = float(detection_result.get("avg_ear", 0.0))
    closed_duration = float(detection_result.get("closed_duration", 0.0))
    yawn_duration = float(detection_result.get("yawn_duration", 0.0))
    distraction_duration = float(detection_result.get("distraction_duration", 0.0))
    fatigue_events = int(detection_result.get("fatigue_events", 0))

    if detection_result.get("drowsy", False):
        score += 75
    elif detection_result.get("eyes_closed", False):
        score += 25 + int(min(35, closed_duration * 12))
    elif avg_ear and avg_ear < 0.22:
        score += 15

    if detection_result.get("distracted", False):
        score += 65
    elif detection_result.get("status") == "LOOKING_AWAY":
        score += 20 + int(min(30, distraction_duration * 10))

    if detection_result.get("fatigued", False):
        score += 55
    elif detection_result.get("yawning", False):
        score += 20 + int(min(25, yawn_duration * 10))

    score += min(25, fatigue_events * 8)
    return max(0, min(100, score))


def get_risk_level(score: int) -> str:
    """Map a 0-100 risk score to a human-readable risk level."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "RISKY"
    if score >= 30:
        return "WARNING"
    return "SAFE"
