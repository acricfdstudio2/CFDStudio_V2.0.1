"""The main menu class that ties all 3D components together."""

from .geometry_primitives import (
    Cone, Cube, Cylinder, Origin, Pyramid, Sketch, Sphere, Vector
)
from .advanced_shapes import AdvancedShapesMenu
from .advanced_templates import AdvancedTemplatesMenu


class ThreeDMenu:
    """Represents the main '3D Menu' API, now plane-aware."""

    def __init__(self):
        self.advanced_templates = AdvancedTemplatesMenu()
        self.advanced_shapes = AdvancedShapesMenu()

    def create_cube(self, side_length: float, plane_context: dict):
        """Creates a logical Cube object."""
        return Cube(side_length, origin=plane_context['origin'])

    def create_sphere(self, radius: float, plane_context: dict):
        """Creates a logical Sphere object."""
        return Sphere(radius, origin=plane_context['origin'])

    def create_cylinder(self, radius: float, height: float, plane_context: dict):
        """Creates a logical Cylinder object."""
        return Cylinder(radius, height, origin=plane_context['origin'])

    def create_cone(self, radius: float, height: float, plane_context: dict):
        """Creates a logical Cone object."""
        return Cone(radius, height, origin=plane_context['origin'])

    def create_pyramid(self, base_sketch_on_buffer: Sketch, height: float,
                       plane_context: dict):
        """Creates a logical Pyramid object."""
        if not isinstance(base_sketch_on_buffer, Sketch):
            raise TypeError("A valid base Sketch is required.")
        return Pyramid(base_sketch_on_buffer, height,
                       origin=plane_context['origin'])

    def create_origin(self):
        """Creates a logical Origin object."""
        return Origin()

    def create_vector(self, x: float, y: float, z: float):
        """Creates a logical Vector object."""
        return Vector(x, y, z)