import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    EAR_THRESHOLD = float(os.getenv("EAR_THRESHOLD", "0.25"))
    EYE_CLOSED_SECONDS = float(os.getenv("EYE_CLOSED_SECONDS", "2.0"))
    MICROSLEEP_SECONDS = float(os.getenv("MICROSLEEP_SECONDS", "0.7"))
    FATIGUE_WINDOW_SECONDS = float(os.getenv("FATIGUE_WINDOW_SECONDS", "120"))
    FATIGUE_MICROSLEEP_COUNT = int(os.getenv("FATIGUE_MICROSLEEP_COUNT", "3"))
    MOUTH_OPEN_THRESHOLD = float(os.getenv("MOUTH_OPEN_THRESHOLD", "0.6"))
    YAWN_SECONDS = float(os.getenv("YAWN_SECONDS", "1.5"))
    FATIGUE_YAWN_COUNT = int(os.getenv("FATIGUE_YAWN_COUNT", "2"))
    HEAD_YAW_RATIO_THRESHOLD = float(os.getenv("HEAD_YAW_RATIO_THRESHOLD", "0.28"))
    HEAD_DOWN_RATIO_THRESHOLD = float(os.getenv("HEAD_DOWN_RATIO_THRESHOLD", "-0.35"))
    DISTRACTION_SECONDS = float(os.getenv("DISTRACTION_SECONDS", "2.0"))
    NO_FACE_SECONDS = float(os.getenv("NO_FACE_SECONDS", "2.0"))
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
