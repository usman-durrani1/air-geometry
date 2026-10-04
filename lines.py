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
CLEAR_COOLDOWN_TIME = 1.0


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

        cv2.line(
            frame,
            anchors[self.start_anchor],
            anchors[self.end_anchor],
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

        self.live_lines = []
        self.fixed_lines = []

        self.left_created = False
        self.right_created = False

        # Contact state
        self.contact_anchors = set()
        self.contact_active = False
        self.structure_created = False

        # Structure state
        self.structure_active = False
        self.structure_anchors = []

        # Hand recovery
        self.hand_missing_since = {
            "left": None,
            "right": None,
        }

        self.structure_hidden = False

        # Clear cooldown
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
    # CREATE BASIC HAND LINES
    # ======================================

    def create_left_line(self):

        if self.cooldown_active():
            return

        if self.left_created:
            return

        # Do not create a new individual
        # pinch line while a structure exists.
        if self.structure_active:
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

        # Do not create a new individual
        # pinch line while a structure exists.
        if self.structure_active:
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
    # CHECK CONNECTION
    # ======================================

    def connected(
        self,
        a,
        b,
        anchors
    ):

        return (
            self.distance(
                anchors[a],
                anchors[b]
            )
            <= CONTACT_DISTANCE
        )

    # ======================================
    # FIND CONNECTED GROUP
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

        # ==================================
        # FOUR POINTS HAVE ABSOLUTE PRIORITY
        # ==================================

        if len(available) == 4:

            connections = {
                name: set()
                for name in available
            }

            for i in range(4):

                for j in range(
                    i + 1,
                    4
                ):

                    first = available[i]
                    second = available[j]

                    if self.connected(
                        first,
                        second,
                        anchors
                    ):

                        connections[first].add(
                            second
                        )

                        connections[second].add(
                            first
                        )

            # Find the connected component.
            visited = set()
            stack = [available[0]]

            while stack:

                current = stack.pop()

                if current in visited:
                    continue

                visited.add(current)

                for neighbor in connections[current]:

                    if neighbor not in visited:
                        stack.append(neighbor)

            if len(visited) == 4:
                return set(available)

        # ==================================
        # THREE POINTS
        # ==================================

        valid_groups = []

        for i in range(
            len(available)
        ):

            for j in range(
                i + 1,
                len(available)
            ):

                for k in range(
                    j + 1,
                    len(available)
                ):

                    group = [
                        available[i],
                        available[j],
                        available[k],
                    ]

                    connected_count = 0

                    for a in range(3):

                        for b in range(
                            a + 1,
                            3
                        ):

                            if self.connected(
                                group[a],
                                group[b],
                                anchors
                            ):

                                connected_count += 1

                    if connected_count == 3:

                        valid_groups.append(
                            set(group)
                        )

        if valid_groups:

            return max(
                valid_groups,
                key=len
            )

        return set()

    # ======================================
    # BUILD TRIANGLE
    # ======================================

    def create_triangle(
        self,
        anchor_names
    ):

        if self.cooldown_active():
            return

        names = list(anchor_names)

        if len(names) != 3:
            return

        # IMPORTANT:
        # Completely remove the old individual
        # hand pinch lines.
        self.live_lines = []

        # Triangle is now the ONLY live structure.
        self.live_lines = [
            LiveLine(
                names[0],
                names[1]
            ),
            LiveLine(
                names[1],
                names[2]
            ),
            LiveLine(
                names[2],
                names[0]
            ),
        ]

        self.structure_active = True

        self.structure_anchors = names

        self.contact_anchors = set(names)

        self.contact_active = True

        self.structure_created = True

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

        # IMPORTANT:
        # Completely remove the triangle and
        # every previous line.
        self.live_lines = []

        # Rectangle is now the ONLY structure.
        self.live_lines = [
            LiveLine(
                "left_thumb",
                "right_thumb"
            ),
            LiveLine(
                "right_thumb",
                "right_index"
            ),
            LiveLine(
                "right_index",
                "left_index"
            ),
            LiveLine(
                "left_index",
                "left_thumb"
            ),
        ]

        self.structure_active = True

        self.structure_anchors = [
            "left_thumb",
            "right_thumb",
            "right_index",
            "left_index",
        ]

        self.contact_anchors = set(
            anchor_names
        )

        self.contact_active = True

        self.structure_created = True

    # ======================================
    # PROCESS CONTACT
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

        # ==================================
        # FOUR POINTS
        #
        # ALWAYS OVERRIDE EVERYTHING.
        # ==================================

        if len(group) == 4:

            self.create_rectangle(
                group
            )

            return

        # ==================================
        # THREE POINTS
        #
        # REMOVE PINCH LINES AND USE ONLY
        # THE TRIANGLE.
        # ==================================

        if len(group) == 3:

            # If a rectangle already exists,
            # do NOT downgrade it.
            if (
                self.structure_active
                and
                len(self.structure_anchors) == 4
            ):
                return

            self.create_triangle(
                group
            )

            return

        # ==================================
        # NO 3/4 POINT STRUCTURE
        # ==================================

        self.contact_active = False

    # ======================================
    # HAND RECOVERY
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

        elif (
            self.hand_missing_since[
                "left"
            ] is None
        ):

            self.hand_missing_since[
                "left"
            ] = now

        if right_present:

            self.hand_missing_since[
                "right"
            ] = None

        elif (
            self.hand_missing_since[
                "right"
            ] is None
        ):

            self.hand_missing_since[
                "right"
            ] = now

        # Hide while required hand is temporarily
        # missing.
        required_hand_missing = False

        for anchor in self.structure_anchors:

            if (
                anchor.startswith("left_")
                and
                not left_present
            ):
                required_hand_missing = True

            if (
                anchor.startswith("right_")
                and
                not right_present
            ):
                required_hand_missing = True

        self.structure_hidden = (
            required_hand_missing
        )

        # Destroy after one second.
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

            if (
                now - missing_since
                >= HAND_RECOVERY_TIME
            ):

                self.destroy_structure()

                return

    # ======================================
    # DESTROY STRUCTURE
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

        if self.cooldown_active():
            return

        # Re-evaluate contact every frame.
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

        if self.cooldown_active():
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
                    anchors[
                        line.start_anchor
                    ],
                    anchors[
                        line.end_anchor
                    ]
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

        self.clear_cooldown_started = (
            time.perf_counter()
        )

    # ======================================
    # DRAW FIXED
    # ======================================

    def draw_fixed(
        self,
        frame
    ):

        if self.cooldown_active():
            return

        for line in self.fixed_lines:

            line.draw(
                frame
            )
