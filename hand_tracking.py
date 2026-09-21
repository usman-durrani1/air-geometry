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


# How strongly the new detection affects
# the previous position.
SMOOTHING_ALPHA = 0.35

# Keep the last good hand briefly when
# MediaPipe temporarily loses it.
HAND_HOLD_TIME = 0.25


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

        self.smoothed_points = {
            "left": None,
            "right": None,
        }

        self.last_seen = {
            "left": 0.0,
            "right": 0.0,
        }

        self.last_hands = {
            "left": None,
            "right": None,
        }

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

    def _smooth_points(
        self,
        label,
        points
    ):

        previous = self.smoothed_points[label]

        if previous is None:

            smoothed = [
                [float(x), float(y)]
                for x, y in points
            ]

        else:

            smoothed = []

            for old, new in zip(
                previous,
                points
            ):

                x = (
                    old[0]
                    +
                    (
                        new[0] - old[0]
                    )
                    * SMOOTHING_ALPHA
                )

                y = (
                    old[1]
                    +
                    (
                        new[1] - old[1]
                    )
                    * SMOOTHING_ALPHA
                )

                smoothed.append(
                    [x, y]
                )

        self.smoothed_points[label] = smoothed

        return [
            (
                int(point[0]),
                int(point[1])
            )
            for point in smoothed
        ]

    def process_hands(
        self,
        result,
        width,
        height
    ):

        now = time.perf_counter()

        detected = {}

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

            raw_points = []

            for landmark in landmarks:

                raw_points.append(
                    (
                        landmark.x * width,
                        landmark.y * height
                    )
                )

            points = self._smooth_points(
                label,
                raw_points
            )

            detected[label] = {
                "landmarks": points,

                "thumb": points[4],
                "index": points[8],
                "middle": points[12],
                "ring": points[16],
                "pinky": points[20],
            }

            self.last_seen[label] = now
            self.last_hands[label] = (
                detected[label]
            )

        # Short recovery window.
        #
        # If MediaPipe loses a hand for a
        # very brief moment, keep the last
        # stable position instead of making
        # it instantly disappear.

        hands = {}

        for label in (
            "left",
            "right"
        ):

            if label in detected:

                hands[label] = detected[label]

                continue

            if (
                self.last_hands[label] is not None
                and
                now - self.last_seen[label]
                <= HAND_HOLD_TIME
            ):

                hands[label] = self.last_hands[label]

        return hands


def extract_hands(
    result,
    width,
    height
):
    """
    Compatibility wrapper.

    Main.py can continue calling
    extract_hands(), while the actual
    smoothing is handled by HandTracker.
    """

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
            "middle": points[12],
            "ring": points[16],
            "pinky": points[20],
        }

    return hands


def draw_hand(
    frame,
    hand
):

    points = hand["landmarks"]

    # -------------------------------
    # Skeleton
    # -------------------------------

    for start, end in HAND_CONNECTIONS:

        cv2.line(
            frame,
            points[start],
            points[end],
            GREEN,
            HAND_LINE_THICKNESS,
            cv2.LINE_AA
        )

    # -------------------------------
    # Normal landmarks
    # -------------------------------

    for point in points:

        cv2.circle(
            frame,
            point,
            LANDMARK_RADIUS,
            GREEN,
            -1,
            cv2.LINE_AA
        )

    # -------------------------------
    # Control points
    # -------------------------------

    control_radius = int(
        CONTROL_DOT_RADIUS * 2
    )

    control_points = [

        hand["thumb"],
        hand["index"],
        hand["middle"],
        hand["ring"],
        hand["pinky"],

    ]

    for point in control_points:

        cv2.circle(
            frame,
            point,
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