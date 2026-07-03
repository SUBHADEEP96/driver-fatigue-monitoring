def calculate_confidence_score(detection_result: dict) -> int:
    """Convert eye metrics into a 0-100 confidence score."""
    if not detection_result.get("face_detected", False):
        return 0

    avg_ear = float(detection_result.get("avg_ear", 0.0))
    closed_duration = float(detection_result.get("closed_duration", 0.0))

    score = 100

    if avg_ear < 0.15:
        score -= 70
    elif avg_ear < 0.22:
        score -= 45
    elif avg_ear < 0.3:
        score -= 20

    score += int(min(25, closed_duration * 8))
    score = max(0, min(100, score))
    return score


def get_risk_level(score: int) -> str:
    """Map a confidence score to a human-readable risk level."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "RISKY"
    if score >= 35:
        return "WARNING"
    return "SAFE"
