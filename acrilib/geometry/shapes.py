"""
Module defining the abstract base class and concrete implementations
for 2D geometric shapes.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

# MERGED: The BasicShape ABC was merged from basic_shape.py for better cohesion.
class BasicShape(ABC):
    """Abstract base class for all 2D geometric entities from file imports."""

    def __init__(self, entity_data: dict):
        """Initializes the basic shape with common DXF attributes."""
        self.layer: str = entity_data.get('layer', '0')
        self.color: int = entity_data.get('color', 256)

    @abstractmethod
    def get_type(self) -> str:
        """Returns the shape type as an uppercase string (e.g., 'LINE')."""
        pass


Point3D = Tuple[float, float, float]
Vertices = List[Point3D]


class Line(BasicShape):
    """Represents a 3D line entity."""
    def __init__(self, entity_data: dict):
        super().__init__(entity_data)
        self.start_point: Point3D = entity_data.get('start_point', (0, 0, 0))
        self.end_point: Point3D = entity_data.get('end_point', (0, 0, 0))

    def get_type(self) -> str:
        return "LINE"


class Circle(BasicShape):
    """Represents a 3D circle entity."""
    def __init__(self, entity_data: dict):
        super().__init__(entity_data)
        self.center: Point3D = entity_data.get('center', (0, 0, 0))
        self.radius: float = entity_data.get('radius', 0.0)

    def get_type(self) -> str:
        return "CIRCLE"


class Arc(Circle):
    """Represents a 3D arc entity, inheriting from Circle."""
    def __init__(self, entity_data: dict):
        super().__init__(entity_data)
        self.start_angle: float = entity_data.get('start_angle', 0.0)
        self.end_angle: float = entity_data.get('end_angle', 360.0)

    def get_type(self) -> str:
        return "ARC"


class LwPolyline(BasicShape):
    """Represents a lightweight polyline (a series of connected 2D vertices)."""
    def __init__(self, entity_data: dict):
        super().__init__(entity_data)
        self.vertices: Vertices = entity_data.get('vertices', [])
        self.is_closed: bool = entity_data.get('closed', False)

    def get_type(self) -> str:
        return "LWPOLYLINE"


class Text(BasicShape):
    """Represents a text entity."""
    def __init__(self, entity_data: dict):
        super().__init__(entity_data)
        self.insertion_point: Point3D = entity_data.get('insertion_point', (0, 0, 0))
        self.text_string: str = entity_data.get('text_string', '')
        self.height: float = entity_data.get('height', 1.0)

    def get_type(self) -> str:
        return "TEXT"