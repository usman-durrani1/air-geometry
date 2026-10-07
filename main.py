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

ONE_HAND_CONFIRMATION_TIME = 0.3


def build_anchors(hands):

    anchors = {}

    if "left" in hands:

        anchors["left_thumb"] = hands["left"]["thumb"]
        anchors["left_index"] = hands["left"]["index"]

    if "right" in hands:

        anchors["right_thumb"] = hands["right"]["thumb"]
        anchors["right_index"] = hands["right"]["index"]

    return anchors


def one_hand_candidate(gesture):

    return (
        gesture is not None
        and
        gesture["thumb"]
        and
        gesture["index"]
        and
        gesture["middle"]
        and
        not gesture["ring"]
        and
        not gesture["pinky"]
    )


def normal_implant_gesture(gesture):

    return (
        gesture is not None
        and
        gesture["thumb"]
        and
        gesture["index"]
        and
        not gesture["middle"]
        and
        not gesture["ring"]
        and
        not gesture["pinky"]
    )


def gesture_name(gesture):

    if gesture is None:
        return "NO HAND"

    if gesture["full_fist"]:
        return "FULL FIST"

    if gesture["implant"]:
        return "IMPLANT"

    if gesture["pinch"]:
        return "PINCH"

    return "NONE"


def state_text(value):

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

    cv2.putText(
        frame,
        side.upper(),
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
            "Thumb": state_text(gesture["thumb"]),
            "Index": state_text(gesture["index"]),
            "Middle": state_text(gesture["middle"]),
            "Ring": state_text(gesture["ring"]),
            "Pinky": state_text(gesture["pinky"]),
        }

        current_gesture = gesture_name(gesture)

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
    cooldown,
    left_check,
    right_check,
    left_active,
    right_active
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

    y = 490

    if left_check:

        cv2.putText(
            frame,
            "LEFT: ONE-HAND CHECK",
            (
                width - panel_width + 12,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 22

    if right_check:

        cv2.putText(
            frame,
            "RIGHT: ONE-HAND CHECK",
            (
                width - panel_width + 12,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 22

    if left_active:

        cv2.putText(
            frame,
            "LEFT: ONE-HAND ACTIVE",
            (
                width - panel_width + 12,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 22

    if right_active:

        cv2.putText(
            frame,
            "RIGHT: ONE-HAND ACTIVE",
            (
                width - panel_width + 12,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 22

    if cooldown:

        cv2.putText(
            frame,
            "CLEAR COOLDOWN",
            (
                width - panel_width + 12,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )


def main():

    print("Air Geometry")
    print("Pinch thumb + index to CREATE a line.")
    print("Thumb + index OPEN, other fingers CLOSED = IMPLANT.")
    print("All five fingers CLOSED = CLEAR.")
    print("One-hand geometry starts after 1 second.")
    print("Press Q to quit.")

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

    left_one_hand_start = None
    right_one_hand_start = None

    previous_left_one_hand = False
    previous_right_one_hand = False

    last_time = time.perf_counter()

    fps = 0.0

    try:

        while True:

            frame = camera.read()

            if frame is None:
                break

            height, width = frame.shape[:2]

            result = tracker.detect(frame)

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
                    in enumerate(result.handedness)
                    if (
                        categories
                        and
                        categories[0]
                        .display_name
                        .lower()
                        == "left"
                    )
                )

                left_gesture = analyze_gestures(
                    result.hand_landmarks[left_index]
                )

            if "right" in hands:

                right_index = next(
                    i
                    for i, categories
                    in enumerate(result.handedness)
                    if (
                        categories
                        and
                        categories[0]
                        .display_name
                        .lower()
                        == "right"
                    )
                )

                right_gesture = analyze_gestures(
                    result.hand_landmarks[right_index]
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

            anchors = build_anchors(hands)

            # ==================================
            # ONE-HAND CONFIRMATION
            # ==================================

            now = time.perf_counter()

            # ----------------------------------
            # LEFT
            # ----------------------------------

            if one_hand_candidate(left_gesture):

                if left_one_hand_start is None:

                    left_one_hand_start = now

                elif (
                    not lines.one_hand_active["left"]
                    and
                    now - left_one_hand_start
                    >= ONE_HAND_CONFIRMATION_TIME
                ):

                    lines.start_one_hand(
                        "left",
                        anchors
                    )

            else:

                if (
                    left_one_hand_start is not None
                    and
                    not lines.one_hand_active["left"]
                    and
                    normal_implant_gesture(left_gesture)
                ):

                    lines.implant_hand(
                        "left",
                        anchors
                    )

                left_one_hand_start = None

            # ----------------------------------
            # RIGHT
            # ----------------------------------

            if one_hand_candidate(right_gesture):

                if right_one_hand_start is None:

                    right_one_hand_start = now

                elif (
                    not lines.one_hand_active["right"]
                    and
                    now - right_one_hand_start
                    >= ONE_HAND_CONFIRMATION_TIME
                ):

                    lines.start_one_hand(
                        "right",
                        anchors
                    )

            else:

                if (
                    right_one_hand_start is not None
                    and
                    not lines.one_hand_active["right"]
                    and
                    normal_implant_gesture(right_gesture)
                ):

                    lines.implant_hand(
                        "right",
                        anchors
                    )

                right_one_hand_start = None

            # ==================================
            # ONE-HAND ACTIVE UPDATE
            # ==================================

            if lines.one_hand_active["left"]:

                left_thumb_closed = (
                    left_gesture is not None
                    and
                    not left_gesture["thumb"]
                )

                lines.update_one_hand(
                    "left",
                    anchors,
                    left_thumb_closed
                )

            if lines.one_hand_active["right"]:

                right_thumb_closed = (
                    right_gesture is not None
                    and
                    not right_gesture["thumb"]
                )

                lines.update_one_hand(
                    "right",
                    anchors,
                    right_thumb_closed
                )

            # ==================================
            # DRAW LIVE STRUCTURE
            # ==================================

            lines.draw_live(
                frame,
                anchors
            )

            # ==================================
            # NORMAL IMPLANT
            # ==================================

            if (
                left_implant
                and
                not previous_left_implant
                and
                not lines.one_hand_active["left"]
                and
                left_one_hand_start is None
            ):

                lines.implant_hand(
                    "left",
                    anchors
                )

            if (
                right_implant
                and
                not previous_right_implant
                and
                not lines.one_hand_active["right"]
                and
                right_one_hand_start is None
            ):

                lines.implant_hand(
                    "right",
                    anchors
                )

            # ==================================
            # ONE-HAND IMPLANT
            # ==================================

            if (
                left_implant
                and
                not previous_left_implant
                and
                lines.one_hand_active["left"]
            ):

                lines.implant_one_hand(
                    "left",
                    anchors
                )

            if (
                right_implant
                and
                not previous_right_implant
                and
                lines.one_hand_active["right"]
            ):

                lines.implant_one_hand(
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

                left_one_hand_start = None

            if (
                right_clear
                and
                not previous_right_clear
            ):

                if not lines.cooldown_active():
                    lines.clear()

                right_one_hand_start = None

            # ==================================
            # DRAW FIXED
            # ==================================

            lines.draw_fixed(frame)

            # ==================================
            # FPS
            # ==================================

            now = time.perf_counter()

            elapsed = now - last_time

            if elapsed > 0:

                current_fps = 1.0 / elapsed

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
                lines.cooldown_active(),
                left_one_hand_start is not None,
                right_one_hand_start is not None,
                lines.one_hand_active["left"],
                lines.one_hand_active["right"]
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

            previous_left_pinch = left_pinch
            previous_right_pinch = right_pinch

            previous_left_implant = left_implant
            previous_right_implant = right_implant

            previous_left_clear = left_clear
            previous_right_clear = right_clear

            previous_left_one_hand = (
                lines.one_hand_active["left"]
            )

            previous_right_one_hand = (
                lines.one_hand_active["right"]
            )

    finally:

        tracker.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
