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

HAND_RECOVERY_TIME = 1.0

# After clearing with a fist, drawing is
# completely disabled for this amount of time.
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
        end
    ):

        self.start = start
        self.end = end

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

        # Lines currently controlled
        # by the user's hands.
        self.live_lines = []

        # Lines permanently implanted
        # onto the screen.
        self.fixed_lines = []

        # Which local hand structures
        # have been created.
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

        # Time at which the clear cooldown began.
        self.clear_cooldown_started = None

    # ======================================
    # CLEAR COOLDOWN
    # ======================================

    def cooldown_active(self):

        if self.clear_cooldown_started is None:
            return False

        elapsed = (
            time.perf_counter()
            -
            self.clear_cooldown_started
        )

        if elapsed >= CLEAR_COOLDOWN_TIME:

            self.clear_cooldown_started = None

            return False

        return True

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

        if self.cooldown_active():
            return set()

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

        # Find pairs of dots that are
        # physically close enough.
        for i in range(
            len(available)
        ):

            for j in range(
                i + 1,
                len(available)
            ):

                pair = {
                    available[i],
                    available[j],
                }

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
                        pair
                    )

        if len(connected) < 3:
            return set()

        connected_list = list(
            connected
        )

        valid_group = set()

        # Check every possible 3-dot group.
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

        # If all four dots are mutually
        # connected, keep all four.
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

        if self.cooldown_active():
            return

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

    # ======================================
    # BUILD RECTANGLE
    # ======================================

    def create_rectangle(
        self,
        anchor_names
    ):

        if self.cooldown_active():
            return

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

    # ======================================
    # PROCESS DOT CONTACT
    # ======================================

    def process_contact(
        self,
        anchors
    ):

        if self.cooldown_active():
            return

        group = self.find_connected_group(
            anchors
        )

        # No three-dot connection.
        if len(group) < 3:

            # If the dots separated after
            # a valid contact, create the
            # stored structure.
            if (
                self.contact_active
                and
                not self.structure_created
                and
                len(self.contact_anchors) >= 3
            ):

                if len(
                    self.contact_anchors
                ) == 4:

                    self.create_rectangle(
                        self.contact_anchors
                    )

                elif len(
                    self.contact_anchors
                ) == 3:

                    self.create_triangle(
                        self.contact_anchors
                    )

                self.structure_created = True

            self.contact_active = False

            return

        self.contact_active = True

        # Four dots always take priority.
        if len(group) == 4:

            self.contact_anchors = set(
                group
            )

        elif len(group) == 3:

            if len(
                self.contact_anchors
            ) < 4:

                self.contact_anchors = set(
                    group
                )

        self.structure_created = False

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

        # ----------------------------------
        # LEFT HAND
        # ----------------------------------

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

        # ----------------------------------
        # RIGHT HAND
        # ----------------------------------

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

        # ----------------------------------
        # DETERMINE WHETHER STRUCTURE
        # SHOULD BE HIDDEN
        # ----------------------------------

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

        # ----------------------------------
        # 1 SECOND EXPIRATION
        # ----------------------------------

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
    # DESTROY ONLY CURRENT STRUCTURE
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

        # During clear cooldown absolutely
        # nothing can be drawn or constructed.
        if self.cooldown_active():

            return

        if (
            not self.structure_active
        ):

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
    # IMPLANT
    # ======================================

    def implant(
        self,
        anchors
    ):

        # Do not allow implantation during
        # the clear cooldown.
        if self.cooldown_active():
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

        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

    # ======================================
    # CLEAR
    # ======================================

    def clear(self):

        # Clear everything immediately.
        self.live_lines = []

        self.fixed_lines = []

        self.left_created = False
        self.right_created = False

        self.contact_anchors = set()

        self.contact_active = False
        self.structure_created = False

        self.structure_active = False
        self.structure_anchors = []

        self.structure_hidden = False

        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

        # Start the 1-second drawing lock.
        self.clear_cooldown_started = (
            time.perf_counter()
        )

    # ======================================
    # DRAW IMPLANTED
    # ======================================

    def draw_fixed(
        self,
        frame
    ):

        # The clear operation already removes
        # all fixed lines. This check also makes
        # the cooldown visually absolute.
        if self.cooldown_active():
            return

        for line in self.fixed_lines:

            line.draw(
                frame
            )
