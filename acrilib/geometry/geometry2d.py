"""Module for the 2D geometry container class."""

from .shapes import Arc, Circle, Line, LwPolyline, Text


class Geometry2D:
    """A container for 2D geometry, typically loaded from a file like DXF."""

    def __init__(self):
        """Initializes the shape list."""
        self.shapes: list = []

    def add_line(self, data: dict):
        """Adds a Line shape."""
        self.shapes.append(Line(data))

    def add_circle(self, data: dict):
        """Adds a Circle shape."""
        self.shapes.append(Circle(data))

    def add_arc(self, data: dict):
        """Adds an Arc shape."""
        self.shapes.append(Arc(data))

    def add_lwpolyline(self, data: dict):
        """Adds a LwPolyline shape."""
        self.shapes.append(LwPolyline(data))

    def add_text(self, data: dict):
        """Adds a Text shape."""
        self.shapes.append(Text(data))

    def get_number_of_shapes(self) -> int:
        """Returns the total number of shapes in the container."""
        return len(self.shapes)