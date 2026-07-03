import math


def euclidean_distance(point_1, point_2) -> float:
    return math.dist(point_1, point_2)


def calculate_ear(eye_points) -> float:
    if len(eye_points) != 6:
        return 0.0

    p1, p2, p3, p4, p5, p6 = eye_points

    vertical_1 = euclidean_distance(p2, p6)
    vertical_2 = euclidean_distance(p3, p5)
    horizontal = euclidean_distance(p1, p4)

    if horizontal == 0:
        return 0.0

    return (vertical_1 + vertical_2) / (2.0 * horizontal)