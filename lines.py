import cv2
import time

from config import (
    WHITE,
    WHITE_LINE_THICKNESS,
    CONTROL_DOT_RADIUS,
)


CONTACT_DISTANCE = max(
    8,
    int(CONTROL_DOT_RADIUS * 3)
)

HAND_RECOVERY_TIME = 1.5
CLEAR_COOLDOWN_TIME = 1.0
ONE_HAND_PINCH_DISTANCE = max(
    10,
    int(CONTROL_DOT_RADIUS * 2)
)


class LiveLine:

    def __init__(
        self,
        start_anchor,
        end_anchor
    ):

        self.start_anchor = start_anchor
        self.end_anchor = end_anchor

    def draw(
        self,
        frame,
        anchors
    ):

        if (
            self.start_anchor not in anchors
            or
            self.end_anchor not in anchors
        ):
            return

        start = anchors[self.start_anchor]
        end = anchors[self.end_anchor]

        cv2.line(
            frame,
            start,
            end,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )


class FixedLine:

    def __init__(
        self,
        start,
        end,
        owner=None
    ):

        self.start = start
        self.end = end
        self.owner = owner

    def draw(self, frame):

        cv2.line(
            frame,
            self.start,
            self.end,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )


class LineSystem:

    def __init__(self):

        self.live_lines = []
        self.fixed_lines = []

        self.left_created = False
        self.right_created = False

        # --------------------------------------
        # NORMAL TWO-HAND STRUCTURES
        # --------------------------------------

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None

        # --------------------------------------
        # HAND RECOVERY
        # --------------------------------------

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

        self.structure_hidden = False

        # --------------------------------------
        # CLEAR COOLDOWN
        # --------------------------------------

        self.clear_time = None

        # --------------------------------------
        # ONE-HAND GEOMETRY
        # --------------------------------------

        self.one_hand_active = {
            "left": False,
            "right": False,
        }

        self.one_hand_planted = {
            "left": None,
            "right": None,
        }

        self.one_hand_shape = {
            "left": None,
            "right": None,
        }

        self.one_hand_thumb_closed = {
            "left": False,
            "right": False,
        }

    # ======================================
    # COOLDOWN
    # ======================================

    def cooldown_active(self):

        if self.clear_time is None:
            return False

        return (
            time.perf_counter()
            - self.clear_time
            <
            CLEAR_COOLDOWN_TIME
        )

    # ======================================
    # NORMAL LINE CREATION
    # ======================================

    def create_left_line(self):

        if self.cooldown_active():
            return

        if self.left_created:
            return

        self.live_lines.append(
            LiveLine(
                "left_thumb",
                "left_index"
            )
        )

        self.left_created = True

    def create_right_line(self):

        if self.cooldown_active():
            return

        if self.right_created:
            return

        self.live_lines.append(
            LiveLine(
                "right_thumb",
                "right_index"
            )
        )

        self.right_created = True

    # ======================================
    # DISTANCE
    # ======================================

    def distance(self, a, b):

        dx = a[0] - b[0]
        dy = a[1] - b[1]

        return (
            dx * dx +
            dy * dy
        ) ** 0.5

    # ======================================
    # TWO-HAND CONNECTED GROUP
    # ======================================

    def find_connected_group(self, anchors):

        if not (
            self.left_created
            and
            self.right_created
        ):
            return set()

        names = [
            "left_thumb",
            "left_index",
            "right_thumb",
            "right_index",
        ]

        available = [
            name
            for name in names
            if name in anchors
        ]

        if len(available) < 3:
            return set()

        connected = set()

        for i in range(len(available)):

            for j in range(i + 1, len(available)):

                if (
                    self.distance(
                        anchors[available[i]],
                        anchors[available[j]]
                    )
                    <= CONTACT_DISTANCE
                ):

                    connected.update({
                        available[i],
                        available[j]
                    })

        if len(connected) < 3:
            return set()

        connected_list = list(connected)
        valid_group = set()

        for i in range(len(connected_list)):

            for j in range(i + 1, len(connected_list)):

                for k in range(j + 1, len(connected_list)):

                    group = [
                        connected_list[i],
                        connected_list[j],
                        connected_list[k],
                    ]

                    all_close = True

                    for a in range(3):

                        for b in range(a + 1, 3):

                            if (
                                self.distance(
                                    anchors[group[a]],
                                    anchors[group[b]]
                                )
                                >
                                CONTACT_DISTANCE
                            ):

                                all_close = False

                    if all_close:
                        valid_group.update(group)

        # Four points always win.
        if len(available) == 4:

            all_four_close = True

            for i in range(4):

                for j in range(i + 1, 4):

                    if (
                        self.distance(
                            anchors[available[i]],
                            anchors[available[j]]
                        )
                        >
                        CONTACT_DISTANCE
                    ):

                        all_four_close = False

            if all_four_close:
                return set(available)

        return valid_group

    # ======================================
    # TWO-HAND TRIANGLE
    # ======================================

    def create_triangle(self, anchor_names):

        names = list(anchor_names)

        if len(names) != 3:
            return

        self.live_lines = []

        self.live_lines.append(
            LiveLine(
                names[0],
                names[1]
            )
        )

        self.live_lines.append(
            LiveLine(
                names[1],
                names[2]
            )
        )

        self.live_lines.append(
            LiveLine(
                names[2],
                names[0]
            )
        )

        self.structure_active = True
        self.structure_anchors = names
        self.structure_type = "triangle"

    # ======================================
    # TWO-HAND RECTANGLE
    # ======================================

    def create_rectangle(self, anchor_names):

        required = {
            "left_thumb",
            "left_index",
            "right_thumb",
            "right_index",
        }

        if set(anchor_names) != required:
            return

        self.live_lines = []

        self.live_lines.append(
            LiveLine(
                "left_thumb",
                "right_thumb"
            )
        )

        self.live_lines.append(
            LiveLine(
                "right_thumb",
                "right_index"
            )
        )

        self.live_lines.append(
            LiveLine(
                "right_index",
                "left_index"
            )
        )

        self.live_lines.append(
            LiveLine(
                "left_index",
                "left_thumb"
            )
        )

        self.structure_active = True

        self.structure_anchors = [
            "left_thumb",
            "right_thumb",
            "right_index",
            "left_index",
        ]

        self.structure_type = "rectangle"

    # ======================================
    # TWO-HAND CONTACT
    # ======================================

    def process_contact(self, anchors):

        group = self.find_connected_group(
            anchors
        )

        if len(group) == 4:

            self.contact_active = True
            self.contact_anchors = set(group)

            self.create_rectangle(group)

            self.structure_created = True

            return

        if len(group) == 3:

            self.contact_active = True
            self.contact_anchors = set(group)

            if not self.structure_active:

                self.create_triangle(group)

                self.structure_created = True

            return

        self.contact_active = False

    # ======================================
    # HAND RECOVERY
    # ======================================

    def update_hand_recovery(self, anchors):

        if not self.structure_active:
            return

        now = time.perf_counter()

        left_present = (
            "left_thumb" in anchors
            and
            "left_index" in anchors
        )

        right_present = (
            "right_thumb" in anchors
            and
            "right_index" in anchors
        )

        if left_present:
            self.hand_missing_since["left"] = None
        else:
            if self.hand_missing_since["left"] is None:
                self.hand_missing_since["left"] = now

        if right_present:
            self.hand_missing_since["right"] = None
        else:
            if self.hand_missing_since["right"] is None:
                self.hand_missing_since["right"] = now

        required_hand_missing = False

        for anchor in self.structure_anchors:

            if anchor.startswith("left_") and not left_present:
                required_hand_missing = True

            if anchor.startswith("right_") and not right_present:
                required_hand_missing = True

        self.structure_hidden = required_hand_missing

        for side in ("left", "right"):

            missing_since = self.hand_missing_since[side]

            if missing_since is None:
                continue

            if (
                now - missing_since
                >= HAND_RECOVERY_TIME
            ):

                self.destroy_structure()
                return

    # ======================================
    # DESTROY TWO-HAND STRUCTURE
    # ======================================

    def destroy_structure(self):

        self.live_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None

        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

    # ======================================
    # ONE-HAND GEOMETRY
    # ======================================

    def start_one_hand(self, hand, anchors):

        if self.cooldown_active():
            return

        thumb_name = hand + "_thumb"
        index_name = hand + "_index"

        if (
            thumb_name not in anchors
            or
            index_name not in anchors
        ):
            return

        thumb = anchors[thumb_name]
        index = anchors[index_name]

        # Remove the normal moving line for this hand.
        # One-hand geometry now owns the line.
        self.live_lines = [
            line
            for line in self.live_lines
            if not (
                line.start_anchor in {
                    thumb_name,
                    index_name,
                }
                and
                line.end_anchor in {
                    thumb_name,
                    index_name,
                }
            )
        ]

        self.one_hand_planted[hand] = (
            thumb,
            index
        )

        self.one_hand_active[hand] = True
        self.one_hand_shape[hand] = "rectangle"
        self.one_hand_thumb_closed[hand] = False

    def update_one_hand(
        self,
        hand,
        anchors,
        thumb_closed=False
    ):

        if not self.one_hand_active[hand]:
            return

        thumb_name = hand + "_thumb"
        index_name = hand + "_index"

        if (
            thumb_name not in anchors
            or
            index_name not in anchors
        ):
            return

        # ----------------------------------
        # RECTANGLE -> TRIANGLE
        # ----------------------------------

        pinch_distance = self.distance(
            anchors[thumb_name],
            anchors[index_name]
        )

        if pinch_distance <= ONE_HAND_PINCH_DISTANCE:

            self.one_hand_thumb_closed[hand] = True

            # This transition belongs ONLY to
            # the one-hand geometry system.
            self.one_hand_shape[hand] = "triangle"

            # Make absolutely sure the normal
            # thumb-index LiveLine cannot reappear.
            self.live_lines = [
                line
                for line in self.live_lines
                if not (
                    line.start_anchor in {
                        thumb_name,
                        index_name,
                    }
                    and
                    line.end_anchor in {
                        thumb_name,
                        index_name,
                    }
                )
            ]

            return

        # ----------------------------------
        # NORMAL ONE-HAND RECTANGLE
        # ----------------------------------

        self.one_hand_thumb_closed[hand] = False

        if self.one_hand_shape[hand] != "triangle":
            self.one_hand_shape[hand] = "rectangle"

    # ======================================
    # DRAW ONE-HAND GEOMETRY
    # ======================================

    def draw_one_hand(
        self,
        frame,
        hand,
        anchors
    ):

        if not self.one_hand_active[hand]:
            return

        planted = self.one_hand_planted[hand]

        if planted is None:
            return

        thumb_name = hand + "_thumb"
        index_name = hand + "_index"

        if index_name not in anchors:
            return

        planted_thumb, planted_index = planted
        current_index = anchors[index_name]

        # ----------------------------------
        # PLANTED LINE
        # ----------------------------------

        cv2.line(
            frame,
            planted_thumb,
            planted_index,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )

        # ----------------------------------
        # TRIANGLE
        # ----------------------------------

        if self.one_hand_shape[hand] == "triangle":

            cv2.line(
                frame,
                planted_thumb,
                current_index,
                WHITE,
                WHITE_LINE_THICKNESS,
                cv2.LINE_AA
            )

            cv2.line(
                frame,
                planted_index,
                current_index,
                WHITE,
                WHITE_LINE_THICKNESS,
                cv2.LINE_AA
            )

            return

        # ----------------------------------
        # RECTANGLE
        # ----------------------------------

        if thumb_name not in anchors:
            return

        current_thumb = anchors[thumb_name]

        # Current moving thumb -> index line.
        cv2.line(
            frame,
            current_thumb,
            current_index,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )

        # Planted thumb -> current thumb.
        cv2.line(
            frame,
            planted_thumb,
            current_thumb,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )

        # Planted index -> current index.
        cv2.line(
            frame,
            planted_index,
            current_index,
            WHITE,
            WHITE_LINE_THICKNESS,
            cv2.LINE_AA
        )

    # ======================================
    # ONE-HAND IMPLANT
    # ======================================

    def implant_one_hand(
        self,
        hand,
        anchors
    ):

        if not self.one_hand_active[hand]:
            return

        planted = self.one_hand_planted[hand]

        if planted is None:
            return

        planted_thumb, planted_index = planted

        thumb_name = hand + "_thumb"
        index_name = hand + "_index"

        if index_name not in anchors:
            return

        current_index = anchors[index_name]

        # ----------------------------------
        # TRIANGLE
        # ----------------------------------

        if self.one_hand_shape[hand] == "triangle":

            self.fixed_lines.append(
                FixedLine(
                    planted_thumb,
                    planted_index,
                    owner=hand
                )
            )

            self.fixed_lines.append(
                FixedLine(
                    planted_thumb,
                    current_index,
                    owner=hand
                )
            )

            self.fixed_lines.append(
                FixedLine(
                    planted_index,
                    current_index,
                    owner=hand
                )
            )

        # ----------------------------------
        # RECTANGLE
        # ----------------------------------

        else:

            if thumb_name not in anchors:
                return

            current_thumb = anchors[thumb_name]

            self.fixed_lines.append(
                FixedLine(
                    planted_thumb,
                    planted_index,
                    owner=hand
                )
            )

            self.fixed_lines.append(
                FixedLine(
                    planted_thumb,
                    current_thumb,
                    owner=hand
                )
            )

            self.fixed_lines.append(
                FixedLine(
                    current_thumb,
                    current_index,
                    owner=hand
                )
            )

            self.fixed_lines.append(
                FixedLine(
                    current_index,
                    planted_index,
                    owner=hand
                )
            )

        self.cancel_one_hand(hand)

    # ======================================
    # CANCEL ONE-HAND
    # ======================================

    def cancel_one_hand(self, hand):

        self.one_hand_active[hand] = False
        self.one_hand_planted[hand] = None
        self.one_hand_shape[hand] = None
        self.one_hand_thumb_closed[hand] = False

    # ======================================
    # NORMAL LIVE DRAW
    # ======================================

    def draw_live(self, frame, anchors):

        # ----------------------------------
        # EXISTING TWO-HAND SYSTEM
        # ----------------------------------

        if (
            not self.one_hand_active["left"]
            and
            not self.one_hand_active["right"]
        ):

            if not self.structure_active:
                self.process_contact(anchors)

        # Four-point priority.
        if (
            self.left_created
            and
            self.right_created
            and
            not self.one_hand_active["left"]
            and
            not self.one_hand_active["right"]
        ):

            group = self.find_connected_group(anchors)

            if len(group) == 4:

                self.create_rectangle(group)

                self.contact_anchors = set(group)
                self.structure_created = True

        self.update_hand_recovery(anchors)

        if not self.structure_hidden:

            for line in self.live_lines:

                line.draw(
                    frame,
                    anchors
                )

        # ----------------------------------
        # ONE-HAND SYSTEM
        # ----------------------------------

        self.draw_one_hand(
            frame,
            "left",
            anchors
        )

        self.draw_one_hand(
            frame,
            "right",
            anchors
        )

    # ======================================
    # NORMAL IMPLANT RECTANGLE
    # ======================================

    def implant_rectangle(self, anchors):

        if (
            not self.structure_active
            or
            self.structure_type != "rectangle"
        ):
            return

        for line in self.live_lines:

            if (
                line.start_anchor not in anchors
                or
                line.end_anchor not in anchors
            ):
                continue

            self.fixed_lines.append(
                FixedLine(
                    anchors[line.start_anchor],
                    anchors[line.end_anchor],
                    owner="rectangle"
                )
            )

        self.live_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None
        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

    # ======================================
    # NORMAL IMPLANT TRIANGLE
    # ======================================

    def implant_triangle(self, anchors):

        if (
            not self.structure_active
            or
            self.structure_type != "triangle"
        ):
            return

        for line in self.live_lines:

            if (
                line.start_anchor not in anchors
                or
                line.end_anchor not in anchors
            ):
                continue

            self.fixed_lines.append(
                FixedLine(
                    anchors[line.start_anchor],
                    anchors[line.end_anchor],
                    owner="triangle"
                )
            )

        self.live_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None
        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

    # ======================================
    # NORMAL HAND IMPLANT
    # ======================================

    def implant_hand(self, hand, anchors):

        # One-hand geometry has priority.
        if self.one_hand_active[hand]:

            self.implant_one_hand(
                hand,
                anchors
            )

            return

        # Existing two-hand rectangle.
        if (
            self.structure_active
            and
            self.structure_type == "rectangle"
        ):

            self.implant_rectangle(anchors)
            return

        # Existing two-hand triangle.
        if (
            self.structure_active
            and
            self.structure_type == "triangle"
        ):

            self.implant_triangle(anchors)
            return

        prefix = hand + "_"

        remaining_lines = []

        for line in self.live_lines:

            start_is_hand = line.start_anchor.startswith(prefix)
            end_is_hand = line.end_anchor.startswith(prefix)

            if not (start_is_hand or end_is_hand):

                remaining_lines.append(line)
                continue

            if (
                line.start_anchor not in anchors
                or
                line.end_anchor not in anchors
            ):

                remaining_lines.append(line)
                continue

            self.fixed_lines.append(
                FixedLine(
                    anchors[line.start_anchor],
                    anchors[line.end_anchor],
                    owner=hand
                )
            )

        self.live_lines = remaining_lines

        if hand == "left":
            self.left_created = False

        if hand == "right":
            self.right_created = False

    # ======================================
    # IMPLANT ALL
    # ======================================

    def implant(self, anchors):

        for line in self.live_lines:

            if (
                line.start_anchor not in anchors
                or
                line.end_anchor not in anchors
            ):
                continue

            self.fixed_lines.append(
                FixedLine(
                    anchors[line.start_anchor],
                    anchors[line.end_anchor]
                )
            )

        self.live_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None
        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

        self.cancel_one_hand("left")
        self.cancel_one_hand("right")

    # ======================================
    # CLEAR
    # ======================================

    def clear(self):

        self.live_lines = []
        self.fixed_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []
        self.structure_type = None

        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

        self.cancel_one_hand("left")
        self.cancel_one_hand("right")

        self.clear_time = time.perf_counter()

    # ======================================
    # DRAW FIXED
    # ======================================

    def draw_fixed(self, frame):

        for line in self.fixed_lines:

            line.draw(frame)
