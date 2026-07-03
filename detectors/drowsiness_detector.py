import time
import cv2
import mediapipe as mp

from config.settings import settings
from detectors.eye_utils import calculate_ear


class DrowsinessDetector:
    """
    Lightweight drowsiness detector using MediaPipe FaceMesh.
    """

    LEFT_EYE_INDEXES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDEXES = [362, 385, 387, 263, 373, 380]

    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.eye_closed_start_time = None

    def _get_pixel_point(self, landmarks, index, frame_width, frame_height):
        landmark = landmarks[index]
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y

    def process_frame(self, frame):
        frame_height, frame_width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb_frame)

        if not result.multi_face_landmarks:
            self.eye_closed_start_time = None

            return {
                "face_detected": False,
                "left_ear": 0.0,
                "right_ear": 0.0,
                "avg_ear": 0.0,
                "eyes_closed": False,
                "drowsy": False,
                "closed_duration": 0.0,
                "status": "NO_FACE",
            }

        face_landmarks = result.multi_face_landmarks[0].landmark

        left_eye_points = [
            self._get_pixel_point(face_landmarks, index, frame_width, frame_height)
            for index in self.LEFT_EYE_INDEXES
        ]

        right_eye_points = [
            self._get_pixel_point(face_landmarks, index, frame_width, frame_height)
            for index in self.RIGHT_EYE_INDEXES
        ]

        left_ear = calculate_ear(left_eye_points)
        right_ear = calculate_ear(right_eye_points)
        avg_ear = (left_ear + right_ear) / 2.0

        eyes_closed = avg_ear < settings.EAR_THRESHOLD

        if eyes_closed:
            if self.eye_closed_start_time is None:
                self.eye_closed_start_time = time.time()

            closed_duration = time.time() - self.eye_closed_start_time
        else:
            self.eye_closed_start_time = None
            closed_duration = 0.0

        drowsy = closed_duration >= settings.EYE_CLOSED_SECONDS

        if drowsy:
            status = "DROWSY"
        elif eyes_closed:
            status = "EYES_CLOSED"
        else:
            status = "AWAKE"

        return {
            "face_detected": True,
            "left_ear": left_ear,
            "right_ear": right_ear,
            "avg_ear": avg_ear,
            "eyes_closed": eyes_closed,
            "drowsy": drowsy,
            "closed_duration": closed_duration,
            "status": status,
        }