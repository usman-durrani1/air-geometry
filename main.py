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


def build_anchors(
    hands
):

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


def gesture_name(
    gesture
):

    if gesture is None:
        return "NO HAND"

    if gesture["full_fist"]:
        return "FULL FIST"

    if gesture["implant"]:
        return "IMPLANT"

    if gesture["pinch"]:
        return "PINCH"

    return "NONE"


def state_text(
    value
):

    if value:
        return "OPEN"

    return "CLOSED"


def draw_hand_panel(
    frame,
    side,
    gesture,
    x,
    y
):

    panel_width = 250
    panel_height = 205

    cv2.rectangle(
        frame,
        (x, y),
        (
            x + panel_width,
            y + panel_height
        ),
        (30, 30, 30),
        -1
    )

    cv2.rectangle(
        frame,
        (x, y),
        (
            x + panel_width,
            y + panel_height
        ),
        (255, 255, 255),
        1
    )

    title = side.upper()

    cv2.putText(
        frame,
        title,
        (x + 12, y + 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    if gesture is None:

        values = {
            "Thumb": "NO HAND",
            "Index": "NO HAND",
            "Middle": "NO HAND",
            "Ring": "NO HAND",
            "Pinky": "NO HAND",
        }

        current_gesture = "NO HAND"

    else:

        values = {
            "Thumb": state_text(
                gesture["thumb"]
            ),

            "Index": state_text(
                gesture["index"]
            ),

            "Middle": state_text(
                gesture["middle"]
            ),

            "Ring": state_text(
                gesture["ring"]
            ),

            "Pinky": state_text(
                gesture["pinky"]
            ),
        }

        current_gesture = gesture_name(
            gesture
        )

    row_y = y + 52

    for name, value in values.items():

        cv2.putText(
            frame,
            f"{name}: {value}",
            (x + 12, row_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        row_y += 25

    cv2.putText(
        frame,
        f"Gesture: {current_gesture}",
        (x + 12, y + 185),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.40,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )


def draw_control_panel(
    frame,
    left_gesture,
    right_gesture,
    cooldown
):

    height, width = frame.shape[:2]

    panel_width = 270

    cv2.rectangle(
        frame,
        (
            width - panel_width,
            0
        ),
        (
            width,
            height
        ),
        (20, 20, 20),
        -1
    )

    cv2.putText(
        frame,
        "CONTROL PANEL",
        (
            width - panel_width + 12,
            28
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    draw_hand_panel(
        frame,
        "LEFT",
        left_gesture,
        width - panel_width + 10,
        45
    )

    draw_hand_panel(
        frame,
        "RIGHT",
        right_gesture,
        width - panel_width + 10,
        260
    )

    if cooldown:

        cv2.putText(
            frame,
            "CLEAR COOLDOWN",
            (
                width - panel_width + 12,
                490
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            "Drawing locked: 1.0s",
            (
                width - panel_width + 12,
                515
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )


def main():

    print(
        "Air Geometry"
    )

    print(
        "Pinch thumb + index to CREATE a line."
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
            # GESTURES
            # ==================================

            left_gesture = None
            right_gesture = None

            if "left" in hands:

                left_index = next(
                    i
                    for i, categories
                    in enumerate(
                        result.handedness
                    )
                    if (
                        categories
                        and
                        categories[0]
                        .display_name
                        .lower()
                        == "left"
                    )
                )

                left_gesture = (
                    analyze_gestures(
                        result.hand_landmarks[
                            left_index
                        ]
                    )
                )

            if "right" in hands:

                right_index = next(
                    i
                    for i, categories
                    in enumerate(
                        result.handedness
                    )
                    if (
                        categories
                        and
                        categories[0]
                        .display_name
                        .lower()
                        == "right"
                    )
                )

                right_gesture = (
                    analyze_gestures(
                        result.hand_landmarks[
                            right_index
                        ]
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
            # SEPARATE IMPLANT
            # ==================================

            if (
                left_implant
                and
                not previous_left_implant
            ):

                lines.implant_hand(
                    "left",
                    anchors
                )

            if (
                right_implant
                and
                not previous_right_implant
            ):

                lines.implant_hand(
                    "right",
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

                if not lines.cooldown_active():

                    lines.clear()

            if (
                right_clear
                and
                not previous_right_clear
            ):

                if not lines.cooldown_active():

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

            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # ==================================
            # CONTROL PANEL
            # ==================================

            draw_control_panel(
                frame,
                left_gesture,
                right_gesture,
                lines.cooldown_active()
            )

            cv2.imshow(
                WINDOW_NAME,
                frame
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
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
