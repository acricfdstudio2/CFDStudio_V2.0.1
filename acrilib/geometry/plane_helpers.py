"""Module containing helper functions related to 2D-to-3D plane transformations."""

from typing import List
import numpy as np


def transform_to_plane(u: float, v: float, origin: List[float],
                       u_axis: List[float], v_axis: List[float]) -> List[float]:
    """
    Helper to transform a 2D plane coordinate (u,v) to a 3D world coordinate.

    Formula: P_world = P_origin + u * U_axis + v * V_axis
    """
    origin_v = np.array(origin)
    u_axis_v = np.array(u_axis)
    v_axis_v = np.array(v_axis)
    point_3d = origin_v + u * u_axis_v + v * v_axis_v
    return point_3d.tolist()