import requests

from config.settings import settings


def send_ntfy_alert(message: str, title: str = "Driver FDD Alert") -> bool:
    """Publish a driver alert to the configured ntfy topic."""
    headers = {
        "Title": title,
        "Tags": "warning,car",
        "Priority": "urgent",
    }

    try:
        response = requests.post(
            settings.NTFY_TOPIC_URL,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False
