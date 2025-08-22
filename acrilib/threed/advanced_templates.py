"""Handles the logic for the 'Advanced Templates' submenu (e.g., Pipe, Airfoil)."""

from .geometry_primitives import Airfoil, Pipe, Sketch, Swirler, Vector


class AdvancedTemplatesMenu:
    """Represents the 'Advanced Templates' submenu's logical operations."""

    def create_pipe(self, path_sketch: Sketch, outer_radius: float,
                      inner_radius: float):
        """Creates a logical Pipe object."""
        if not isinstance(path_sketch, Sketch):
            raise TypeError("A valid path Sketch is required.")
        return Pipe(path=path_sketch, outer_radius=outer_radius,
                    inner_radius=inner_radius)

    def create_swirler(self, profile_sketch: Sketch, axis: Vector, twist_angle: float):
        """Creates a logical Swirler object."""
        if not isinstance(profile_sketch, Sketch):
            raise TypeError("A valid profile Sketch is required.")
        return Swirler(profile=profile_sketch, axis=axis, twist_angle=twist_angle)

    def create_airfoil(self, profile_sketch: Sketch, length: float):
        """Creates a logical Airfoil object."""
        if not isinstance(profile_sketch, Sketch):
            raise TypeError("An airfoil profile Sketch is required.")
        return Airfoil(profile=profile_sketch, length=length)