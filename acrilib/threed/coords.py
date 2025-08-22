# File: acrilib/threed/coords.py

"""
Defines the backend logic for creating and managing Local Coordinate Systems (LCS).
"""
import math

# --- Vector Math Helpers ---
# ... (no changes to helper functions)
def subtract_vectors(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])
def cross_product(v1, v2):
    return (v1[1] * v2[2] - v1[2] * v2[1], v1[2] * v2[0] - v1[0] * v2[2], v1[0] * v2[1] - v1[1] * v2[0])
def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
def magnitude(v):
    return math.sqrt(dot_product(v, v))
def normalize(v):
    mag = magnitude(v)
    if mag == 0: raise ValueError("Cannot normalize a zero-magnitude vector.")
    return (v[0] / mag, v[1] / mag, v[2] / mag)

# --- Core Classes ---
class LocalCoordinateSystem:
    # ... (no changes to this class)
    def __init__(self, title, origin, x_axis, y_axis, z_axis):
        self.title = title
        self.origin = origin
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.z_axis = z_axis

    def __repr__(self):
        o = tuple(round(i, 2) for i in self.origin)
        x = tuple(round(i, 2) for i in self.x_axis)
        y = tuple(round(i, 2) for i in self.y_axis)
        return f"CS(Title='{self.title}', Origin={o}, X-Axis={x}, Y-Axis={y})"


class CoordinateSystemManager:
    """Manages the creation, storage, and retrieval of all coordinate systems."""
    def __init__(self):
        self.systems = {"Global": LocalCoordinateSystem("Global", (0,0,0), (1,0,0), (0,1,0), (0,0,1))}
        self.active_cs_title = "Global"

    def get_cs(self, title: str):
        return self.systems.get(title)

    def create_cs_from_3_points(self, title: str, origin, point_on_x, point_in_xy):
        if title in self.systems:
            raise ValueError(f"A Coordinate System with the title '{title}' already exists.")
        try:
            vec_x = normalize(subtract_vectors(point_on_x, origin))
            temp_vec = subtract_vectors(point_in_xy, origin)
            vec_z = normalize(cross_product(vec_x, temp_vec))
            vec_y = normalize(cross_product(vec_z, vec_x))
        except ValueError as e:
            raise ValueError(f"Invalid points provided (they may be collinear). Details: {e}")
        self.systems[title] = LocalCoordinateSystem(title, origin, vec_x, vec_y, vec_z)
        return self.systems[title]

    def create_cs_from_vectors(self, title: str, origin, x_dir, y_dir):
        if title in self.systems:
            raise ValueError(f"A Coordinate System with the title '{title}' already exists.")
        try:
            vec_x = normalize(x_dir)
            vec_z = normalize(cross_product(vec_x, y_dir))
            vec_y = normalize(cross_product(vec_z, vec_x))
        except ValueError as e:
            raise ValueError(f"Invalid vectors provided (they may be parallel or zero). Details: {e}")
        self.systems[title] = LocalCoordinateSystem(title, origin, vec_x, vec_y, vec_z)
        return self.systems[title]

    def set_active(self, title: str):
        if title not in self.systems:
            raise ValueError(f"CS with title '{title}' not found.")
        self.active_cs_title = title

    # --- NEW METHODS ---

    def delete_cs(self, title: str) -> bool:
        """Deletes a CS by its title. Returns False if not found."""
        if title in self.systems:
            del self.systems[title]
            return True
        return False

    def rename_cs(self, old_title: str, new_title: str):
        """Renames a CS, updating its key and internal title property."""
        if new_title in self.systems:
            raise ValueError(f"A Coordinate System with the title '{new_title}' already exists.")
        if old_title not in self.systems:
            raise ValueError(f"The system to rename, '{old_title}', was not found.")
        
        cs = self.systems.pop(old_title)
        cs.title = new_title
        self.systems[new_title] = cs

        # If the renamed CS was active, update the active title
        if self.active_cs_title == old_title:
            self.active_cs_title = new_title

    def reset(self):
        """Resets the manager to its default state with only the Global CS."""
        self.__init__()