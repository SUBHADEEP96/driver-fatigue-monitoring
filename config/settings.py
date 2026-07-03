import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    EAR_THRESHOLD = float(os.getenv("EAR_THRESHOLD", "0.25"))
    EYE_CLOSED_SECONDS = float(os.getenv("EYE_CLOSED_SECONDS", "2.0"))
    ALARM_COOLDOWN_SECONDS = int(os.getenv("ALARM_COOLDOWN_SECONDS", "20"))
    ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    OWNER_WHATSAPP_NUMBER = os.getenv("OWNER_WHATSAPP_NUMBER", "")


settings = Settings()
