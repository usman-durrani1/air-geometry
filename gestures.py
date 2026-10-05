import math

from config import PINCH_DISTANCE


def distance(a, b):

    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return math.sqrt(
        dx * dx +
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

    # --------------------------------------
    # PINCH
    # --------------------------------------

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

    # --------------------------------------
    # IMPLANT
    #
    # Thumb + index OPEN
    # Middle + ring + pinky CLOSED
    # --------------------------------------

    implant = (
        thumb
        and index
        and not middle
        and not ring
        and not pinky
    )

    # --------------------------------------
    # FULL FIST
    #
    # ALL FIVE CLOSED
    # --------------------------------------

    full_fist = (
        not thumb
        and not index
        and not middle
        and not ring
        and not pinky
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
