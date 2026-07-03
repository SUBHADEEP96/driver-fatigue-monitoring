import requests

from config.settings import settings


def send_whatsapp_alert(message: str) -> bool:
    """Send an alert via webhook if WhatsApp is enabled and credentials exist."""
    if not settings.ENABLE_WHATSAPP:
        return False

    token = settings.WHATSAPP_ACCESS_TOKEN
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    recipient = settings.OWNER_WHATSAPP_NUMBER
    if not token or not phone_number_id or not recipient:
        return False

    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message},
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False
