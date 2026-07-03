import time
from collections import deque

import cv2
import mediapipe as mp

from config.settings import settings
from detectors.eye_utils import calculate_ear, euclidean_distance


class DrowsinessDetector:
    """
    Driver-state detector using MediaPipe FaceMesh.

    It detects three operational risk categories:
    - drowsiness: eyes closed longer than the configured duration
    - fatigue: repeated microsleeps or yawning over a rolling window
    - distraction: no face or head turned away from the road for too long
    """

    LEFT_EYE_INDEXES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDEXES = [362, 385, 387, 263, 373, 380]
    MOUTH_INDEXES = [61, 291, 13, 14]
    NOSE_TIP_INDEX = 1
    CHIN_INDEX = 152

    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.eye_closed_start_time = None
        self.no_face_start_time = None
        self.distracted_start_time = None
        self.yawn_start_time = None
        self.microsleep_timestamps = deque()
        self.yawn_timestamps = deque()

    def _get_pixel_point(self, landmarks, index, frame_width, frame_height):
        landmark = landmarks[index]
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y

    def _prune_events(self, events, now):
        while events and now - events[0] > settings.FATIGUE_WINDOW_SECONDS:
            events.popleft()

    def _get_mouth_aspect_ratio(self, landmarks, frame_width, frame_height) -> float:
        left, right, upper, lower = [
            self._get_pixel_point(landmarks, index, frame_width, frame_height)
            for index in self.MOUTH_INDEXES
        ]
        horizontal = euclidean_distance(left, right)
        if horizontal == 0:
            return 0.0
        return euclidean_distance(upper, lower) / horizontal

    def _get_attention_metrics(self, landmarks, frame_width, frame_height) -> tuple[float, float]:
        left_eye_outer = self._get_pixel_point(landmarks, 33, frame_width, frame_height)
        right_eye_outer = self._get_pixel_point(landmarks, 263, frame_width, frame_height)
        nose_tip = self._get_pixel_point(landmarks, self.NOSE_TIP_INDEX, frame_width, frame_height)
        chin = self._get_pixel_point(landmarks, self.CHIN_INDEX, frame_width, frame_height)

        face_width = euclidean_distance(left_eye_outer, right_eye_outer)
        if face_width == 0:
            return 0.0, 0.0

        eye_center_x = (left_eye_outer[0] + right_eye_outer[0]) / 2.0
        yaw_ratio = (nose_tip[0] - eye_center_x) / face_width
        pitch_ratio = (nose_tip[1] - chin[1]) / face_width
        return yaw_ratio, pitch_ratio

    def process_frame(self, frame):
        now = time.time()
        frame_height, frame_width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb_frame)

        if not result.multi_face_landmarks:
            self.eye_closed_start_time = None
            self.distracted_start_time = None
            self.yawn_start_time = None

            if self.no_face_start_time is None:
                self.no_face_start_time = now
            no_face_duration = now - self.no_face_start_time
            distracted = no_face_duration >= settings.NO_FACE_SECONDS

            return {
                "face_detected": False,
                "left_ear": 0.0,
                "right_ear": 0.0,
                "avg_ear": 0.0,
                "mouth_aspect_ratio": 0.0,
                "yaw_ratio": 0.0,
                "pitch_ratio": 0.0,
                "eyes_closed": False,
                "yawning": False,
                "drowsy": False,
                "fatigued": False,
                "distracted": distracted,
                "closed_duration": 0.0,
                "yawn_duration": 0.0,
                "distraction_duration": no_face_duration,
                "fatigue_events": len(self.microsleep_timestamps) + len(self.yawn_timestamps),
                "status": "DISTRACTED" if distracted else "NO_FACE",
            }

        self.no_face_start_time = None
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
        mouth_aspect_ratio = self._get_mouth_aspect_ratio(face_landmarks, frame_width, frame_height)
        yaw_ratio, pitch_ratio = self._get_attention_metrics(face_landmarks, frame_width, frame_height)

        eyes_closed = avg_ear < settings.EAR_THRESHOLD
        if eyes_closed:
            if self.eye_closed_start_time is None:
                self.eye_closed_start_time = now
            closed_duration = now - self.eye_closed_start_time
        else:
            if self.eye_closed_start_time is not None:
                previous_closed_duration = now - self.eye_closed_start_time
                if previous_closed_duration >= settings.MICROSLEEP_SECONDS:
                    self.microsleep_timestamps.append(now)
            self.eye_closed_start_time = None
            closed_duration = 0.0

        yawning = mouth_aspect_ratio >= settings.MOUTH_OPEN_THRESHOLD
        if yawning:
            if self.yawn_start_time is None:
                self.yawn_start_time = now
            yawn_duration = now - self.yawn_start_time
        else:
            if self.yawn_start_time is not None:
                previous_yawn_duration = now - self.yawn_start_time
                if previous_yawn_duration >= settings.YAWN_SECONDS:
                    self.yawn_timestamps.append(now)
            self.yawn_start_time = None
            yawn_duration = 0.0

        looking_away = (
            abs(yaw_ratio) >= settings.HEAD_YAW_RATIO_THRESHOLD
            or pitch_ratio >= settings.HEAD_DOWN_RATIO_THRESHOLD
        )
        if looking_away:
            if self.distracted_start_time is None:
                self.distracted_start_time = now
            distraction_duration = now - self.distracted_start_time
        else:
            self.distracted_start_time = None
            distraction_duration = 0.0

        self._prune_events(self.microsleep_timestamps, now)
        self._prune_events(self.yawn_timestamps, now)

        drowsy = closed_duration >= settings.EYE_CLOSED_SECONDS
        fatigued = (
            len(self.microsleep_timestamps) >= settings.FATIGUE_MICROSLEEP_COUNT
            or len(self.yawn_timestamps) >= settings.FATIGUE_YAWN_COUNT
            or yawn_duration >= settings.YAWN_SECONDS
        )
        distracted = distraction_duration >= settings.DISTRACTION_SECONDS

        if drowsy:
            status = "DROWSY"
        elif distracted:
            status = "DISTRACTED"
        elif fatigued:
            status = "FATIGUED"
        elif eyes_closed:
            status = "EYES_CLOSED"
        elif yawning:
            status = "YAWNING"
        elif looking_away:
            status = "LOOKING_AWAY"
        else:
            status = "SAFE"

        return {
            "face_detected": True,
            "left_ear": left_ear,
            "right_ear": right_ear,
            "avg_ear": avg_ear,
            "mouth_aspect_ratio": mouth_aspect_ratio,
            "yaw_ratio": yaw_ratio,
            "pitch_ratio": pitch_ratio,
            "eyes_closed": eyes_closed,
            "yawning": yawning,
            "drowsy": drowsy,
            "fatigued": fatigued,
            "distracted": distracted,
            "closed_duration": closed_duration,
            "yawn_duration": yawn_duration,
            "distraction_duration": distraction_duration,
            "fatigue_events": len(self.microsleep_timestamps) + len(self.yawn_timestamps),
            "status": status,
        }
