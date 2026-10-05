import cv2
import time
import mediapipe as mp

from config import (
    MODEL_PATH,
    NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_PRESENCE_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    GREEN,
    RED,
    HAND_LINE_THICKNESS,
    LANDMARK_RADIUS,
    CONTROL_DOT_RADIUS,
)


BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


HAND_CONNECTIONS = [

    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),

    (5, 9),
    (9, 13),
    (13, 17),
]


class HandTracker:

    def __init__(self):

        options = HandLandmarkerOptions(

            base_options=BaseOptions(
                model_asset_path=MODEL_PATH
            ),

            running_mode=VisionRunningMode.VIDEO,

            num_hands=NUM_HANDS,

            min_hand_detection_confidence=(
                MIN_DETECTION_CONFIDENCE
            ),

            min_hand_presence_confidence=(
                MIN_PRESENCE_CONFIDENCE
            ),

            min_tracking_confidence=(
                MIN_TRACKING_CONFIDENCE
            ),
        )

        self.landmarker = (
            HandLandmarker
            .create_from_options(options)
        )

        self.start_time = time.perf_counter()
        self.last_timestamp_ms = 0

    def detect(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(
            (
                time.perf_counter()
                - self.start_time
            ) * 1000
        )

        if timestamp_ms <= self.last_timestamp_ms:

            timestamp_ms = (
                self.last_timestamp_ms + 1
            )

        self.last_timestamp_ms = timestamp_ms

        return self.landmarker.detect_for_video(
            image,
            timestamp_ms
        )

    def close(self):

        self.landmarker.close()


def extract_hands(
    result,
    width,
    height
):

    hands = {}

    for i, landmarks in enumerate(
        result.hand_landmarks
    ):

        if i >= len(result.handedness):
            continue

        categories = result.handedness[i]

        if not categories:
            continue

        label = (
            categories[0]
            .display_name
            .lower()
        )

        if label not in (
            "left",
            "right"
        ):
            continue

        points = []

        for landmark in landmarks:

            points.append(
                (
                    int(
                        landmark.x * width
                    ),
                    int(
                        landmark.y * height
                    )
                )
            )

        hands[label] = {
            "landmarks": points,
            "thumb": points[4],
            "index": points[8],
        }

    return hands


def draw_hand(
    frame,
    hand
):

    points = hand["landmarks"]

    # Skeleton
    for start, end in HAND_CONNECTIONS:

        cv2.line(
            frame,
            points[start],
            points[end],
            GREEN,
            HAND_LINE_THICKNESS,
            cv2.LINE_AA
        )

    # Landmarks
    for point in points:

        cv2.circle(
            frame,
            point,
            LANDMARK_RADIUS,
            GREEN,
            -1,
            cv2.LINE_AA
        )

    # Control points
    control_radius = int(
        CONTROL_DOT_RADIUS * 2
    )

    cv2.circle(
        frame,
        hand["thumb"],
        control_radius,
        RED,
        -1,
        cv2.LINE_AA
    )

    cv2.circle(
        frame,
        hand["index"],
        control_radius,
        RED,
        -1,
        cv2.LINE_AA
    )


def draw_hands(
    frame,
    hands
):

    for hand in hands.values():

        draw_hand(
            frame,
            hand
        )
