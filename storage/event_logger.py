from datetime import datetime


def log_event(
    status: str,
    score: int,
    risk_level: str,
    avg_ear: float,
    closed_duration: float,
    yawn_duration: float = 0.0,
    distraction_duration: float = 0.0,
    fatigue_events: int = 0,
) -> None:
    """Append an event entry to the local event log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("events.log", "a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp} | status={status} | score={score} | risk_level={risk_level} | "
            f"avg_ear={avg_ear:.3f} | closed_duration={closed_duration:.1f} | "
            f"yawn_duration={yawn_duration:.1f} | "
            f"distraction_duration={distraction_duration:.1f} | "
            f"fatigue_events={fatigue_events}\n"
        )
