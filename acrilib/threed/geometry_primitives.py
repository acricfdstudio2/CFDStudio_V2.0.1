"""
Defines placeholder classes for logical geometric entities.

These represent the 'idea' of a shape, distinct from its visual VTK representation.
3D shapes are aware of their origin on a specific plane.
"""


class Sketch:
    """A placeholder class representing a 2D sketch selected by the user."""
    def __init__(self, name="Unnamed Sketch", points=None, origin=None):
        self.name = name
        self.points = points or []
        self.origin = origin if origin is not None else [0, 0, 0]
        print(f"INFO: Created or selected Sketch: '{self.name}'")

    def __repr__(self):
        return f"Sketch(name='{self.name}', points={len(self.points)})"


class Vector:
    """Represents a 3D vector."""
    def __init__(self, x=0, y=0, z=1):
        self.x, self.y, self.z = x, y, z
        print(f"INFO: Created Vector({self.x}, {self.y}, {self.z})")

    def __repr__(self):
        return f"Vector(x={self.x}, y={self.y}, z={self.z})"


class Origin:
    """Represents the coordinate system origin."""
    def __init__(self):
        self.x, self.y, self.z = 0, 0, 0
        print("INFO: Created Origin at (0, 0, 0)")

    def __repr__(self):
        return "Origin(0, 0, 0)"


class ThreeDShape:
    """Base class for all 3D shapes, now with an origin."""
    def __init__(self, name, origin=None):
        self.name = name
        self.origin = origin if origin is not None else [0, 0, 0]
        print(f"SUCCESS: Created 3D Shape -> {self.name} at origin {self.origin}")

    def __repr__(self):
        return f"3D Shape: {self.name}"


class Cube(ThreeDShape):
    def __init__(self, side_length, origin):
        super().__init__(f"Cube(side={side_length})", origin)


class Sphere(ThreeDShape):
    def __init__(self, radius, origin):
        super().__init__(f"Sphere(radius={radius})", origin)


class Cylinder(ThreeDShape):
    def __init__(self, radius, height, origin):
        super().__init__(f"Cylinder(r={radius}, h={height})", origin)


class Cone(ThreeDShape):
    def __init__(self, radius, height, origin):
        super().__init__(f"Cone(r={radius}, h={height})", origin)


class Pyramid(ThreeDShape):
    def __init__(self, base_sketch, height, origin):
        super().__init__(f"Pyramid(base={base_sketch}, h={height})", origin)


class Pipe(ThreeDShape):
    def __init__(self, path, outer_radius, inner_radius):
        super().__init__(f"Pipe(path={path.name}, OD={outer_radius}, ID={inner_radius})",
                         path.origin)


class Swirler(ThreeDShape):
    def __init__(self, profile, axis, twist_angle):
        super().__init__(f"Swirler(profile={profile.name}, twist={twist_angle} deg)",
                         profile.origin)


class Airfoil(ThreeDShape):
    def __init__(self, profile, length):
        super().__init__(f"Airfoil(profile={profile.name}, length={length})",
                         profile.origin)


class Extrude(ThreeDShape):
    def __init__(self, sketch, depth):
        super().__init__(f"Extrude(sketch='{sketch.name}', depth={depth})",
                         sketch.origin)


class Revolve(ThreeDShape):
    def __init__(self, sketch, axis, angle):
        super().__init__(f"Revolve(sketch='{sketch.name}', angle={angle})",
                         sketch.origin)


class Sweep(ThreeDShape):
    def __init__(self, profile, path):
        super().__init__(f"Sweep(profile='{profile.name}', path='{path.name}')",
                         profile.origin)


class Loft(ThreeDShape):
    def __init__(self, profiles):
        profile_names = [p.name for p in profiles]
        super().__init__(f"Loft(profiles={profile_names})", profiles[0].origin)