"""Handles the logic for the 'Advanced Shapes' submenu (e.g., Extrude, Revolve)."""

from typing import List
from .geometry_primitives import Extrude, Loft, Revolve, Sketch, Sweep, Vector


class AdvancedShapesMenu:
    """Represents the 'Advanced Shapes' submenu's logical operations."""

    def extrude(self, sketch_on_buffer: Sketch, depth: float):
        """Creates a logical Extrude object."""
        if not isinstance(sketch_on_buffer, Sketch):
            raise TypeError("A valid Sketch must be on the buffer.")
        return Extrude(sketch=sketch_on_buffer, depth=depth)

    def revolve(self, sketch_on_buffer: Sketch, axis: Vector,
                  angle: float = 360.0):
        """Creates a logical Revolve object."""
        if not isinstance(sketch_on_buffer, Sketch):
            raise TypeError("A valid Sketch must be on the buffer.")
        return Revolve(sketch=sketch_on_buffer, axis=axis, angle=angle)

    def sweep(self, profile_sketch_on_buffer: Sketch, path_sketch: Sketch):
        """Creates a logical Sweep object."""
        if not isinstance(profile_sketch_on_buffer, Sketch) or \
           not isinstance(path_sketch, Sketch):
            raise TypeError("A valid profile and path Sketch are required.")
        return Sweep(profile=profile_sketch_on_buffer, path=path_sketch)

    def loft(self, sketches: List[Sketch]):
        """Creates a logical Loft object."""
        if not all(isinstance(s, Sketch) for s in sketches) or len(sketches) < 2:
            raise TypeError("At least two valid Sketches are required.")
        return Loft(profiles=sketches)