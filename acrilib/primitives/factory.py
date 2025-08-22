# File: acrilib/primitives/factory.py
"""A factory module for creating primitive geometry data structures for visualization."""

import math
from typing import Any, Dict, List

import numpy as np
import vtk

from ..geometry.plane_helpers import transform_to_plane

GeomData = Dict[str, Any]
Vector3D = List[float]


def create_plane_geometry_data(origin: Vector3D, normal: Vector3D,
                               size: float = 10.0) -> GeomData: # MODIFIED: Default size is now 10
    """Creates geometry data for a visual plane and includes its definition."""
    plane_source = vtk.vtkPlaneSource()
    plane_source.SetCenter(origin)
    plane_source.SetNormal(normal)

    u_axis, v_axis = np.zeros(3), np.zeros(3)
    vtk.vtkMath.Perpendiculars(normal, u_axis, v_axis, 0)

    plane_source.SetPoint1(np.array(origin) + size * u_axis)
    plane_source.SetPoint2(np.array(origin) + size * v_axis)
    plane_source.Update()

    polydata = plane_source.GetOutput()
    points = [list(polydata.GetPoint(i)) for i in range(polydata.GetNumberOfPoints())]
    # A plane source creates a single polygon cell
    cell_points = polydata.GetCell(0).GetPointIds()
    cell_indices = [cell_points.GetId(j) for j in range(cell_points.GetNumberOfIds())]

    return {
        'points': points,
        'cells': [cell_indices],
        'type': 'polys',
        # This definition is crucial for state management
        'definition': {'origin': origin, 'normal': normal}
    }


def create_point(u: float, v: float, plane_context: dict) -> GeomData:
    """Creates geometry for a single 3D point on a plane."""
    point_3d = transform_to_plane(u, v, **plane_context)
    return {'points': [point_3d], 'cells': [[0]], 'type': 'verts'}


def create_line(u1: float, v1: float, u2: float, v2: float, plane_context: dict) -> GeomData:
    """Creates geometry for a single 3D line on a plane."""
    p1 = transform_to_plane(u1, v1, **plane_context)
    p2 = transform_to_plane(u2, v2, **plane_context)
    return {'points': [p1, p2], 'cells': [[0, 1]], 'type': 'lines'}


def create_triangle(u1, v1, u2, v2, u3, v3, plane_context: dict) -> GeomData:
    """Creates geometry for a single 3D triangle on a plane."""
    p1 = transform_to_plane(u1, v1, **plane_context)
    p2 = transform_to_plane(u2, v2, **plane_context)
    p3 = transform_to_plane(u3, v3, **plane_context)
    return {'points': [p1, p2, p3], 'cells': [[0, 1, 2]], 'type': 'polys'}


def create_circle(cu, cv, r, plane_context: dict, segments=100) -> GeomData:
    """Creates a line-strip representation of a circle on a plane."""
    points = []
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        u = cu + r * math.cos(angle)
        v = cv + r * math.sin(angle)
        points.append(transform_to_plane(u, v, **plane_context))

    cell = list(range(segments + 1))
    return {'points': points, 'cells': [cell], 'type': 'lines'}


def create_cuboid(size: float, plane_context: dict) -> GeomData:
    """Creates a 2D wireframe representation of a square on a plane."""
    d = size 
    local_points = [
        [-d, -d, 0], [d, -d, 0], [d, d, 0], [-d, d, 0]
    ]
    points_3d = [transform_to_plane(p[0], p[1], **plane_context) for p in local_points]
    return {'points': points_3d, 'cells': [[0, 1, 2, 3, 0]], 'type': 'lines'}


def create_origin_marker(size: float) -> List[GeomData]:
    """Creates three colored lines for X, Y, Z axes at the global origin."""
    origin = [0.0, 0.0, 0.0]
    x_axis = {
        'points': [origin, [size, 0, 0]], 'cells': [[0, 1]],
        'type': 'lines', 'color': (1, 0, 0)
    }
    y_axis = {
        'points': [origin, [0, size, 0]], 'cells': [[0, 1]],
        'type': 'lines', 'color': (0, 1, 0)
    }
    z_axis = {
        'points': [origin, [0, 0, size]], 'cells': [[0, 1]],
        'type': 'lines', 'color': (0, 0, 1)
    }
    return [x_axis, y_axis, z_axis]


def _extract_polydata(polydata: vtk.vtkPolyData) -> GeomData:
    """Helper function to extract points and cells from a vtkPolyData object."""
    points = [list(polydata.GetPoint(i)) for i in range(polydata.GetNumberOfPoints())]
    cells = []
    for i in range(polydata.GetNumberOfPolys()):
        cell_points = polydata.GetCell(i).GetPointIds()
        cells.append([cell_points.GetId(j) for j in range(cell_points.GetNumberOfIds())])
    return {'points': points, 'cells': cells, 'type': 'polys'}


def create_cube_data(side_length: float, plane_context: dict) -> GeomData:
    """Returns data for a 3D cube oriented and centered on the plane."""
    d = side_length 
    local_points = [[-d,-d,-d],[d,-d,-d],[d,d,-d],[-d,d,-d],
                    [-d,-d,d],[d,-d,d],[d,d,d],[-d,d,d]]

    origin = np.array(plane_context['origin'])
    u_axis = np.array(plane_context['u_axis'])
    v_axis = np.array(plane_context['v_axis'])
    w_axis = np.cross(u_axis, v_axis)

    world_points = [(origin + p[0]*u_axis + p[1]*v_axis + p[2]*w_axis).tolist()
                    for p in local_points]
    cells = [[0,1,2,3], [4,5,6,7], [0,1,5,4], [2,3,7,6], [0,3,7,4], [1,2,6,5]]
    return {'points': world_points, 'cells': cells, 'type': 'polys'}


def create_sphere_data(radius: float, plane_context: dict,
                       resolution: int = 20) -> GeomData:
    """Returns data for a 3D sphere centered on the plane's origin."""
    source = vtk.vtkSphereSource()
    source.SetRadius(radius)
    source.SetThetaResolution(resolution)
    source.SetPhiResolution(resolution)
    source.SetCenter(plane_context['origin'])
    source.Update()
    return _extract_polydata(source.GetOutput())


def create_cylinder_data(radius: float, height: float, plane_context: dict,
                         resolution: int = 30) -> GeomData:
    """Returns data for a 3D cylinder oriented along the plane's normal."""
    source = vtk.vtkCylinderSource()
    source.SetRadius(radius)
    source.SetHeight(height)
    source.SetResolution(resolution)
    source.Update()

    origin = np.array(plane_context['origin'])
    normal = np.cross(plane_context['u_axis'], plane_context['v_axis'])
    y_axis = np.array([0, 1, 0])

    if np.allclose(y_axis, normal):
        rotation_axis, angle_rad = np.array([1, 0, 0]), 0
    elif np.allclose(y_axis, -normal):
        rotation_axis, angle_rad = np.array([1, 0, 0]), np.pi
    else:
        rotation_axis = np.cross(y_axis, normal)
        angle_rad = np.arccos(np.dot(y_axis, normal))

    transform = vtk.vtkTransform()
    transform.Translate(origin)
    transform.RotateWXYZ(np.degrees(angle_rad), rotation_axis)

    transformer = vtk.vtkTransformPolyDataFilter()
    transformer.SetTransform(transform)
    transformer.SetInputConnection(source.GetOutputPort())
    transformer.Update()
    return _extract_polydata(transformer.GetOutput())


def create_cone_data(radius: float, height: float, plane_context: dict,
                     resolution: int = 30) -> GeomData:
    """Returns data for a 3D cone oriented along the plane's normal."""
    source = vtk.vtkConeSource()
    source.SetRadius(radius)
    source.SetHeight(height)
    source.SetResolution(resolution)
    source.Update()

    origin = np.array(plane_context['origin'])
    normal = np.cross(plane_context['u_axis'], plane_context['v_axis'])
    y_axis = np.array([0, 1, 0])

    if np.allclose(y_axis, normal):
        rotation_axis, angle_rad = np.array([1, 0, 0]), 0
    elif np.allclose(y_axis, -normal):
        rotation_axis, angle_rad = np.array([1, 0, 0]), np.pi
    else:
        rotation_axis = np.cross(y_axis, normal)
        angle_rad = np.arccos(np.dot(y_axis, normal))

    transform = vtk.vtkTransform()
    transform.Translate(origin)
    transform.RotateWXYZ(np.degrees(angle_rad), rotation_axis)

    transformer = vtk.vtkTransformPolyDataFilter()
    transformer.SetTransform(transform)
    transformer.SetInputConnection(source.GetOutputPort())
    transformer.Update()
    return _extract_polydata(transformer.GetOutput())