import cv2
import time

from camera import Camera
from hand_tracking import (
    HandTracker,
    extract_hands,
    draw_hands,
)

from gestures import analyze_gestures
from lines import LineSystem


WINDOW_NAME = "Air Geometry"

# Right-side status panel
PANEL_WIDTH = 330
PANEL_BACKGROUND = (30, 30, 30)
PANEL_ALPHA = 0.88


def build_anchors(hands):

    anchors = {}

    if "left" in hands:

        anchors["left_thumb"] = (
            hands["left"]["thumb"]
        )

        anchors["left_index"] = (
            hands["left"]["index"]
        )

    if "right" in hands:

        anchors["right_thumb"] = (
            hands["right"]["thumb"]
        )

        anchors["right_index"] = (
            hands["right"]["index"]
        )

    return anchors


def get_hand_landmarks(
    result,
    hand_name
):

    hand_name = hand_name.lower()

    for i, categories in enumerate(
        result.handedness
    ):

        if not categories:
            continue

        label = (
            categories[0]
            .display_name
            .lower()
        )

        if label == hand_name:

            if i < len(result.hand_landmarks):

                return result.hand_landmarks[i]

    return None


def draw_status_panel(
    frame,
    left_gesture,
    right_gesture,
    fps
):

    height, width = frame.shape[:2]

    panel_left = max(
        0,
        width - PANEL_WIDTH
    )

    # ----------------------------------
    # PANEL BACKGROUND
    # ----------------------------------

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (panel_left, 0),
        (width, height),
        PANEL_BACKGROUND,
        -1
    )

    frame[:] = cv2.addWeighted(
        overlay,
        PANEL_ALPHA,
        frame,
        1.0 - PANEL_ALPHA,
        0
    )

    x = panel_left + 18

    # ----------------------------------
    # TITLE
    # ----------------------------------

    y = 30

    cv2.putText(
        frame,
        "AIR GEOMETRY 2.2",
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    y += 30

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (180, 180, 180),
        1,
        cv2.LINE_AA
    )

    y += 30

    # ----------------------------------
    # HAND DISPLAY
    # ----------------------------------

    def draw_hand(
        name,
        gesture
    ):

        nonlocal y

        detected = gesture is not None

        # Hand heading
        cv2.putText(
            frame,
            name,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

        y += 23

        if not detected:

            cv2.putText(
                frame,
                "NOT DETECTED",
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.43,
                (120, 120, 120),
                1,
                cv2.LINE_AA
            )

            y += 35

            return

        cv2.putText(
            frame,
            "DETECTED",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.43,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

        y += 25

        # Finger states
        finger_states = [
            ("T", gesture["thumb"]),
            ("I", gesture["index"]),
            ("M", gesture["middle"]),
            ("R", gesture["ring"]),
            ("P", gesture["pinky"]),
        ]

        for label, is_open in finger_states:

            state = (
                "OPEN"
                if is_open
                else "CLOSED"
            )

            text = f"{label}: {state}"

            cv2.putText(
                frame,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            y += 20

        # Current gesture
        if gesture["pinch"]:

            action = "PINCH / CREATE"

        elif gesture["implant"]:

            action = "IMPLANT"

        elif gesture["full_fist"]:

            action = "FULL FIST / CLEAR"

        else:

            action = "NO GESTURE"

        y += 3

        cv2.putText(
            frame,
            f"Action: {action}",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 35

    draw_hand(
        "LEFT HAND",
        left_gesture
    )

    draw_hand(
        "RIGHT HAND",
        right_gesture
    )


def main():

    print()
    print(
        "================================"
    )
    print(
        "        AIR GEOMETRY 2.2"
    )
    print(
        "================================"
    )
    print()
    print(
        "Pinch thumb + index to CREATE a line."
    )
    print(
        "Release the pinch: the line stays LIVE."
    )
    print(
        "Move your hands to deform the geometry."
    )
    print(
        "Thumb + index OPEN, other fingers CLOSED = IMPLANT."
    )
    print(
        "All five fingers CLOSED = CLEAR."
    )
    print(
        "Press Q to quit."
    )
    print()

    camera = Camera()

    Camera.create_window(
        WINDOW_NAME
    )

    tracker = HandTracker()

    lines = LineSystem()

    previous_left_pinch = False
    previous_right_pinch = False

    previous_left_implant = False
    previous_right_implant = False

    previous_left_clear = False
    previous_right_clear = False

    last_time = time.perf_counter()

    fps = 0.0

    try:

        while True:

            frame = camera.read()

            if frame is None:
                break

            height, width = (
                frame.shape[:2]
            )

            # ==================================
            # HAND TRACKING
            # ==================================

            result = tracker.detect(
                frame
            )

            hands = extract_hands(
                result,
                width,
                height
            )

            draw_hands(
                frame,
                hands
            )

            # ==================================
            # FIND HAND LANDMARKS
            # ==================================

            left_landmarks = (
                get_hand_landmarks(
                    result,
                    "left"
                )
            )

            right_landmarks = (
                get_hand_landmarks(
                    result,
                    "right"
                )
            )

            # ==================================
            # GESTURES
            # ==================================

            left_gesture = None
            right_gesture = None

            if left_landmarks is not None:

                left_gesture = (
                    analyze_gestures(
                        left_landmarks
                    )
                )

            if right_landmarks is not None:

                right_gesture = (
                    analyze_gestures(
                        right_landmarks
                    )
                )

            # ==================================
            # CURRENT STATES
            # ==================================

            left_pinch = (
                left_gesture is not None
                and
                left_gesture["pinch"]
            )

            right_pinch = (
                right_gesture is not None
                and
                right_gesture["pinch"]
            )

            left_implant = (
                left_gesture is not None
                and
                left_gesture["implant"]
            )

            right_implant = (
                right_gesture is not None
                and
                right_gesture["implant"]
            )

            left_clear = (
                left_gesture is not None
                and
                left_gesture["full_fist"]
            )

            right_clear = (
                right_gesture is not None
                and
                right_gesture["full_fist"]
            )

            # ==================================
            # PINCH CREATION
            # ==================================

            if (
                left_pinch
                and
                not previous_left_pinch
            ):

                lines.create_left_line()

            if (
                right_pinch
                and
                not previous_right_pinch
            ):

                lines.create_right_line()

            # ==================================
            # LIVE ANCHORS
            # ==================================

            anchors = build_anchors(
                hands
            )

            # ==================================
            # DRAW LIVE STRUCTURE
            # ==================================

            lines.draw_live(
                frame,
                anchors
            )

            # ==================================
            # IMPLANT
            # ==================================

            if (
                left_implant
                and
                not previous_left_implant
            ):

                lines.implant(
                    anchors
                )

            if (
                right_implant
                and
                not previous_right_implant
            ):

                lines.implant(
                    anchors
                )

            # ==================================
            # CLEAR
            # ==================================

            if (
                left_clear
                and
                not previous_left_clear
            ):

                lines.clear()

            if (
                right_clear
                and
                not previous_right_clear
            ):

                lines.clear()

            # ==================================
            # DRAW FIXED
            # ==================================

            lines.draw_fixed(
                frame
            )

            # ==================================
            # FPS
            # ==================================

            now = time.perf_counter()

            elapsed = (
                now - last_time
            )

            if elapsed > 0:

                current_fps = (
                    1.0 / elapsed
                )

                fps = (
                    fps * 0.9
                    +
                    current_fps * 0.1
                )

            last_time = now

            # ==================================
            # STATUS PANEL
            # ==================================

            draw_status_panel(
                frame,
                left_gesture,
                right_gesture,
                fps
            )

            # ==================================
            # DISPLAY
            # ==================================

            cv2.imshow(
                WINDOW_NAME,
                frame
            )

            key = (
                cv2.waitKey(1)
                &
                0xFF
            )

            if key == ord("q"):
                break

            # ==================================
            # PREVIOUS STATES
            # ==================================

            previous_left_pinch = (
                left_pinch
            )

            previous_right_pinch = (
                right_pinch
            )

            previous_left_implant = (
                left_implant
            )

            previous_right_implant = (
                right_implant
            )

            previous_left_clear = (
                left_clear
            )

            previous_right_clear = (
                right_clear
            )

    finally:

        tracker.close()

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":

    main()
