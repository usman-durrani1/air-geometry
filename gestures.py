import math

from config import PINCH_DISTANCE


def distance(a, b):

    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return math.sqrt(
        dx * dx
        +
        dy * dy
    )


def angle_3d(a, b, c):

    va = (
        a.x - b.x,
        a.y - b.y,
        a.z - b.z
    )

    vc = (
        c.x - b.x,
        c.y - b.y,
        c.z - b.z
    )

    dot = (
        va[0] * vc[0]
        +
        va[1] * vc[1]
        +
        va[2] * vc[2]
    )

    mag_a = math.sqrt(
        va[0] ** 2
        +
        va[1] ** 2
        +
        va[2] ** 2
    )

    mag_c = math.sqrt(
        vc[0] ** 2
        +
        vc[1] ** 2
        +
        vc[2] ** 2
    )

    if mag_a == 0 or mag_c == 0:
        return 0.0

    cosine = dot / (
        mag_a * mag_c
    )

    cosine = max(
        -1.0,
        min(1.0, cosine)
    )

    return math.degrees(
        math.acos(cosine)
    )


def finger_open(
    hand,
    mcp,
    pip,
    tip
):

    return (
        angle_3d(
            hand[mcp],
            hand[pip],
            hand[tip]
        )
        > 135
    )


def thumb_open(hand):

    return (
        angle_3d(
            hand[2],
            hand[3],
            hand[4]
        )
        > 130
    )


# ======================================
# CONSERVATIVE FIST DETECTION
# ======================================

def finger_curling(
    hand,
    mcp,
    pip,
    tip
):

    # A genuinely curled finger should bring
    # its fingertip back toward the palm.
    #
    # We compare the fingertip's distance
    # from the wrist against the PIP joint.
    #
    # This helps distinguish a real fist from
    # a relaxed hand whose fingers are simply
    # slightly curved.

    wrist = hand[0]

    tip_distance = math.sqrt(
        (
            hand[tip].x
            -
            wrist.x
        ) ** 2
        +
        (
            hand[tip].y
            -
            wrist.y
        ) ** 2
        +
        (
            hand[tip].z
            -
            wrist.z
        ) ** 2
    )

    pip_distance = math.sqrt(
        (
            hand[pip].x
            -
            wrist.x
        ) ** 2
        +
        (
            hand[pip].y
            -
            wrist.y
        ) ** 2
        +
        (
            hand[pip].z
            -
            wrist.z
        ) ** 2
    )

    return (
        tip_distance
        <
        pip_distance * 1.05
    )


def thumb_curled(hand):

    # The thumb is treated separately because
    # its natural movement is different from
    # the four fingers.

    wrist = hand[0]

    thumb_tip_distance = math.sqrt(
        (
            hand[4].x
            -
            wrist.x
        ) ** 2
        +
        (
            hand[4].y
            -
            wrist.y
        ) ** 2
        +
        (
            hand[4].z
            -
            wrist.z
        ) ** 2
    )

    index_mcp_distance = math.sqrt(
        (
            hand[5].x
            -
            wrist.x
        ) ** 2
        +
        (
            hand[5].y
            -
            wrist.y
        ) ** 2
        +
        (
            hand[5].z
            -
            wrist.z
        ) ** 2
    )

    return (
        thumb_tip_distance
        <
        index_mcp_distance * 1.25
    )


def genuine_full_fist(
    hand,
    thumb,
    index,
    middle,
    ring,
    pinky
):

    # First requirement:
    # all five fingers must be classified
    # as closed by the existing angle system.

    if (
        thumb
        or
        index
        or
        middle
        or
        ring
        or
        pinky
    ):
        return False

    # Second requirement:
    # the four main fingers must actually
    # curl toward the palm.

    index_curled = finger_curling(
        hand,
        5,
        6,
        8
    )

    middle_curled = finger_curling(
        hand,
        9,
        10,
        12
    )

    ring_curled = finger_curling(
        hand,
        13,
        14,
        16
    )

    pinky_curled = finger_curling(
        hand,
        17,
        18,
        20
    )

    if not (
        index_curled
        and
        middle_curled
        and
        ring_curled
        and
        pinky_curled
    ):
        return False

    # Third requirement:
    # thumb must also be curled into the palm.

    if not thumb_curled(hand):
        return False

    return True


# ======================================
# MAIN GESTURE ANALYSIS
# ======================================

def analyze_gestures(
    landmarks
):

    thumb = thumb_open(
        landmarks
    )

    index = finger_open(
        landmarks,
        5,
        6,
        8
    )

    middle = finger_open(
        landmarks,
        9,
        10,
        12
    )

    ring = finger_open(
        landmarks,
        13,
        14,
        16
    )

    pinky = finger_open(
        landmarks,
        17,
        18,
        20
    )

    # ==================================
    # PINCH
    # ==================================

    thumb_point = (
        int(landmarks[4].x * 1000),
        int(landmarks[4].y * 1000)
    )

    index_point = (
        int(landmarks[8].x * 1000),
        int(landmarks[8].y * 1000)
    )

    pinch = (
        distance(
            thumb_point,
            index_point
        )
        <= 40
    )

    # ==================================
    # IMPLANT
    #
    # Thumb + index OPEN
    # Middle + ring + pinky CLOSED
    # ==================================

    implant = (
        thumb
        and
        index
        and
        not middle
        and
        not ring
        and
        not pinky
    )

    # ==================================
    # FULL FIST
    #
    # Conservative genuine fist detection.
    # ==================================

    full_fist = genuine_full_fist(
        landmarks,
        thumb,
        index,
        middle,
        ring,
        pinky
    )

    return {
        "thumb": thumb,
        "index": index,
        "middle": middle,
        "ring": ring,
        "pinky": pinky,

        "pinch": pinch,

        "implant": implant,

        "full_fist": full_fist,
    }
