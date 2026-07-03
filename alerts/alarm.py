import time


class AlarmController:
    def __init__(self, cooldown_seconds: int = 20):
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered_at = None

    def trigger_alarm(self) -> bool:
        """Trigger the alarm only after the cooldown has elapsed."""
        now = time.time()
        if self.last_triggered_at is not None:
            if now - self.last_triggered_at < self.cooldown_seconds:
                return False

        self.last_triggered_at = now
        return True
