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


class LiveLine:

    def __init__(
        self,
        start_anchor,
        end_anchor
    ):

        self.start_anchor = (
            start_anchor
        )

        self.end_anchor = (
            end_anchor
        )

    def draw(
        self,
        frame,
        anchors
    ):

        if (
            self.start_anchor
            not in anchors
            or
            self.end_anchor
            not in anchors
        ):
            return

        start = anchors[
            self.start_anchor
        ]

        end = anchors[
            self.end_anchor
        ]

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

    def draw(
        self,
        frame
    ):

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
        # CONTACT / SHAPE CREATION
        # --------------------------------------

        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        # --------------------------------------
        # STRUCTURE STATE
        # --------------------------------------

        self.structure_active = False
        self.structure_anchors = []

        # None      = normal lines
        # triangle  = triangle structure
        # rectangle = rectangle structure
        self.structure_type = None

        # --------------------------------------
        # HAND LOSS RECOVERY
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
    # CREATE A HAND LINE
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

    def distance(
        self,
        a,
        b
    ):

        dx = a[0] - b[0]
        dy = a[1] - b[1]

        return (
            dx * dx
            +
            dy * dy
        ) ** 0.5

    # ======================================
    # FIND CONNECTED DOTS
    # ======================================

    def find_connected_group(
        self,
        anchors
    ):

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

        for i in range(
            len(available)
        ):

            for j in range(
                i + 1,
                len(available)
            ):

                if (
                    self.distance(
                        anchors[
                            available[i]
                        ],
                        anchors[
                            available[j]
                        ]
                    )
                    <= CONTACT_DISTANCE
                ):

                    connected.update(
                        {
                            available[i],
                            available[j]
                        }
                    )

        if len(connected) < 3:
            return set()

        connected_list = list(
            connected
        )

        valid_group = set()

        for i in range(
            len(connected_list)
        ):

            for j in range(
                i + 1,
                len(connected_list)
            ):

                for k in range(
                    j + 1,
                    len(connected_list)
                ):

                    group = [
                        connected_list[i],
                        connected_list[j],
                        connected_list[k],
                    ]

                    all_close = True

                    for a in range(3):

                        for b in range(
                            a + 1,
                            3
                        ):

                            if (
                                self.distance(
                                    anchors[
                                        group[a]
                                    ],
                                    anchors[
                                        group[b]
                                    ]
                                )
                                >
                                CONTACT_DISTANCE
                            ):

                                all_close = False

                    if all_close:

                        valid_group.update(
                            group
                        )

        # ----------------------------------
        # FOUR ALWAYS BEATS THREE
        # ----------------------------------

        if len(available) == 4:

            all_four_close = True

            for i in range(4):

                for j in range(
                    i + 1,
                    4
                ):

                    if (
                        self.distance(
                            anchors[
                                available[i]
                            ],
                            anchors[
                                available[j]
                            ]
                        )
                        >
                        CONTACT_DISTANCE
                    ):

                        all_four_close = False

            if all_four_close:

                return set(
                    available
                )

        return valid_group

    # ======================================
    # BUILD TRIANGLE
    # ======================================

    def create_triangle(
        self,
        anchor_names
    ):

        names = list(
            anchor_names
        )

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
    # BUILD RECTANGLE
    # ======================================

    def create_rectangle(
        self,
        anchor_names
    ):

        required = {
            "left_thumb",
            "left_index",
            "right_thumb",
            "right_index",
        }

        if set(anchor_names) != required:
            return

        self.live_lines = []

        # ----------------------------------
        # RECTANGLE SIDES
        # ----------------------------------

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
    # PROCESS DOT CONTACT
    # ======================================

    def process_contact(
        self,
        anchors
    ):

        group = self.find_connected_group(
            anchors
        )

        # ----------------------------------
        # FOUR-POINT PRIORITY
        # ----------------------------------

        if len(group) == 4:

            self.contact_active = True

            self.contact_anchors = set(
                group
            )

            self.create_rectangle(
                group
            )

            self.structure_created = True

            return

        # ----------------------------------
        # THREE-POINT CONTACT
        # ----------------------------------

        if len(group) == 3:

            self.contact_active = True

            self.contact_anchors = set(
                group
            )

            if not self.structure_active:

                self.create_triangle(
                    group
                )

                self.structure_created = True

            return

        # ----------------------------------
        # CONTACT ENDED
        # ----------------------------------

        self.contact_active = False

    # ======================================
    # HAND PRESENCE / RECOVERY
    # ======================================

    def update_hand_recovery(
        self,
        anchors
    ):

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

            self.hand_missing_since[
                "left"
            ] = None

        else:

            if (
                self.hand_missing_since[
                    "left"
                ]
                is None
            ):

                self.hand_missing_since[
                    "left"
                ] = now

        if right_present:

            self.hand_missing_since[
                "right"
            ] = None

        else:

            if (
                self.hand_missing_since[
                    "right"
                ]
                is None
            ):

                self.hand_missing_since[
                    "right"
                ] = now

        required_hand_missing = False

        for anchor in (
            self.structure_anchors
        ):

            if anchor.startswith(
                "left_"
            ):

                if not left_present:
                    required_hand_missing = True

            if anchor.startswith(
                "right_"
            ):

                if not right_present:
                    required_hand_missing = True

        if required_hand_missing:

            self.structure_hidden = True

        else:

            self.structure_hidden = False

        for side in (
            "left",
            "right"
        ):

            missing_since = (
                self.hand_missing_since[
                    side
                ]
            )

            if missing_since is None:
                continue

            elapsed = (
                now - missing_since
            )

            if elapsed >= HAND_RECOVERY_TIME:

                self.destroy_structure()

                return

    # ======================================
    # DESTROY CURRENT STRUCTURE
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
    # DRAW LIVE
    # ======================================

    def draw_live(
        self,
        frame,
        anchors
    ):

        # ----------------------------------
        # IMPORTANT:
        # Check four-point priority even when
        # a triangle already exists.
        # ----------------------------------

        if (
            self.left_created
            and
            self.right_created
        ):

            group = self.find_connected_group(
                anchors
            )

            if len(group) == 4:

                self.create_rectangle(
                    group
                )

                self.contact_anchors = set(
                    group
                )

                self.structure_created = True

        if not self.structure_active:

            self.process_contact(
                anchors
            )

        self.update_hand_recovery(
            anchors
        )

        if self.structure_hidden:
            return

        for line in self.live_lines:

            line.draw(
                frame,
                anchors
            )

    # ======================================
    # IMPLANT RECTANGLE
    # ======================================

    def implant_rectangle(
        self,
        anchors
    ):

        if (
            not self.structure_active
            or
            self.structure_type != "rectangle"
        ):
            return

        for line in self.live_lines:

            if (
                line.start_anchor
                not in anchors
                or
                line.end_anchor
                not in anchors
            ):
                continue

            start = anchors[
                line.start_anchor
            ]

            end = anchors[
                line.end_anchor
            ]

            self.fixed_lines.append(
                FixedLine(
                    start,
                    end,
                    owner="rectangle"
                )
            )

        # ----------------------------------
        # RECTANGLE IS NOW FIXED
        # ----------------------------------

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
    # IMPLANT TRIANGLE
    # ======================================

    def implant_triangle(
        self,
        anchors
    ):

        if (
            not self.structure_active
            or
            self.structure_type != "triangle"
        ):
            return

        for line in self.live_lines:

            if (
                line.start_anchor
                not in anchors
                or
                line.end_anchor
                not in anchors
            ):
                continue

            start = anchors[
                line.start_anchor
            ]

            end = anchors[
                line.end_anchor
            ]

            self.fixed_lines.append(
                FixedLine(
                    start,
                    end,
                    owner="triangle"
                )
            )

        # ----------------------------------
        # TRIANGLE IS NOW FIXED
        # ----------------------------------

        self.live_lines = []

        # Reset BOTH hand states so either
        # hand can immediately create a new line.

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
    # IMPLANT ONE HAND
    # ======================================

    def implant_hand(
        self,
        hand,
        anchors
    ):

        # ==================================
        # SPECIAL RECTANGLE CASE
        # ==================================

        if (
            self.structure_active
            and
            self.structure_type == "rectangle"
        ):

            self.implant_rectangle(
                anchors
            )

            return

        # ==================================
        # SPECIAL TRIANGLE CASE
        # ==================================

        if (
            self.structure_active
            and
            self.structure_type == "triangle"
        ):

            self.implant_triangle(
                anchors
            )

            return

        # ==================================
        # NORMAL LINE BEHAVIOR
        # ==================================

        prefix = hand + "_"

        remaining_lines = []

        for line in self.live_lines:

            start_is_hand = (
                line.start_anchor.startswith(
                    prefix
                )
            )

            end_is_hand = (
                line.end_anchor.startswith(
                    prefix
                )
            )

            if not (
                start_is_hand
                or
                end_is_hand
            ):

                remaining_lines.append(
                    line
                )

                continue

            if (
                line.start_anchor
                not in anchors
                or
                line.end_anchor
                not in anchors
            ):

                remaining_lines.append(
                    line
                )

                continue

            start = anchors[
                line.start_anchor
            ]

            end = anchors[
                line.end_anchor
            ]

            self.fixed_lines.append(
                FixedLine(
                    start,
                    end,
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

    def implant(
        self,
        anchors
    ):

        for line in self.live_lines:

            if (
                line.start_anchor
                not in anchors
                or
                line.end_anchor
                not in anchors
            ):
                continue

            start = anchors[
                line.start_anchor
            ]

            end = anchors[
                line.end_anchor
            ]

            self.fixed_lines.append(
                FixedLine(
                    start,
                    end
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

        self.clear_time = time.perf_counter()

    # ======================================
    # DRAW IMPLANTED
    # ======================================

    def draw_fixed(
        self,
        frame
    ):

        for line in self.fixed_lines:

            line.draw(
                frame
            )
