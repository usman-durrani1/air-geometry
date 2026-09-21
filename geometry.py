from itertools import permutations


def distance(a, b):

    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return (
        dx * dx +
        dy * dy
    ) ** 0.5


def orientation(a, b, c):

    value = (
        (b[0] - a[0]) *
        (c[1] - a[1])
        -
        (b[1] - a[1]) *
        (c[0] - a[0])
    )

    if abs(value) < 1e-6:
        return 0

    return 1 if value > 0 else 2


def segments_intersect(
    a,
    b,
    c,
    d
):

    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)

    return (
        o1 != o2
        and
        o3 != o4
    )


def is_simple_polygon(points):

    if len(points) != 4:
        return False

    if segments_intersect(
        points[0],
        points[1],
        points[2],
        points[3]
    ):
        return False

    if segments_intersect(
        points[1],
        points[2],
        points[3],
        points[0]
    ):
        return False

    return True


def polygon_perimeter(points):

    total = 0.0

    for i in range(
        len(points)
    ):

        total += distance(
            points[i],
            points[
                (i + 1)
                % len(points)
            ]
        )

    return total


def order_four_points(points):

    if len(points) != 4:
        return None

    best = None

    best_perimeter = float(
        "inf"
    )

    first = points[0]

    for remaining in permutations(
        points[1:]
    ):

        candidate = (
            first,
            *remaining
        )

        if not is_simple_polygon(
            candidate
        ):
            continue

        perimeter = (
            polygon_perimeter(
                candidate
            )
        )

        if perimeter < best_perimeter:

            best = candidate

            best_perimeter = (
                perimeter
            )

    if best is None:
        return None

    return list(best)