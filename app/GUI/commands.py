# File: app/GUI/commands.py
"""
Defines the Command Pattern interface and classes for enabling robust,
multi-level undo/redo functionality. Each user action that modifies the
scene state is encapsulated as a command object.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import vtk
from PyQt5.QtCore import Qt

from acrilib.primitives import factory as primitives
from acrilib.readers.dxf_reader import DxfReader

if TYPE_CHECKING:
    from .main_window import MainWindow


class ICommand(ABC):
    """Abstract base class (Interface) for the Command Pattern."""
    @abstractmethod
    def execute(self) -> None: pass
    @abstractmethod
    def undo(self) -> None: pass


class CreateObjectCommand(ICommand):
    """Command to create and add a VTK actor to the scene."""
    def __init__(self, main_window: 'MainWindow', geom_data: dict, **kwargs):
        self.main_window = main_window
        self.renderer = main_window.renderer
        self.obj_browser = main_window.object_browser
        self.geom_data = geom_data
        self.properties = kwargs
        self.actor: vtk.vtkActor | None = None
        self.category: str = kwargs.get('category', 'Primitives')
        self.object_id: str = kwargs.get('object_name', f"{self.category.rstrip('s')}_{id(self)}")

    def execute(self) -> None:
        if self.actor:
            self.renderer.AddActor(self.actor)
            self.main_window.actor_buffer[self.object_id] = self.actor
            self.obj_browser.add_object(self.object_id, self.geom_data.get('type', 'Import'), self.category)
            if self.category == 'Planes': self.main_window.plane_definitions[self.object_id] = self.geom_data['definition']
            return
        try:
            if 'actor' in self.geom_data:
                self.actor = self.geom_data['actor']
            else:
                vtk_points = vtk.vtkPoints()
                for p in self.geom_data['points']: vtk_points.InsertNextPoint(p)
                cell_array = vtk.vtkCellArray()
                cell_type = self.geom_data['type']
                for cell_indices in self.geom_data['cells']:
                    if cell_type == "verts": cell = vtk.vtkVertex()
                    elif cell_type == "lines": cell = vtk.vtkLine()
                    elif cell_type == "polys": cell = vtk.vtkPolygon()
                    else: continue
                    cell.GetPointIds().SetNumberOfIds(len(cell_indices))
                    for i, point_id in enumerate(cell_indices): cell.GetPointIds().SetId(i, point_id)
                    cell_array.InsertNextCell(cell)
                poly_data = vtk.vtkPolyData()
                poly_data.SetPoints(vtk_points)
                if cell_type == "verts": poly_data.SetVerts(cell_array)
                elif cell_type == "lines": poly_data.SetLines(cell_array)
                elif cell_type == "polys": poly_data.SetPolys(cell_array)
                mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly_data)
                self.actor = vtk.vtkActor(); self.actor.SetMapper(mapper)
            prop = self.actor.GetProperty()
            prop.SetColor(self.properties.get('color', (1, 1, 1)))
            prop.SetPointSize(self.properties.get('point_size', 5))
            prop.SetLineWidth(self.properties.get('line_width', 2))
            prop.SetOpacity(self.properties.get('opacity', 1.0))
            if self.properties.get('representation') == 'wireframe': prop.SetRepresentationToWireframe()
            self.renderer.AddActor(self.actor)
            self.obj_browser.add_object(self.object_id, self.geom_data.get('type', 'Unknown'), self.category)
            self.main_window.actor_buffer[self.object_id] = self.actor
            if self.category == 'Planes' and 'definition' in self.geom_data:
                self.main_window.plane_definitions[self.object_id] = self.geom_data['definition']
        except Exception as e:
            print(f"Error executing CreateObjectCommand: {e}")
            self.actor = None

    def undo(self) -> None:
        if self.actor:
            self.renderer.RemoveActor(self.actor)
            self.obj_browser.remove_object(self.object_id)
            if self.object_id in self.main_window.actor_buffer: del self.main_window.actor_buffer[self.object_id]
            if self.object_id in self.main_window.plane_definitions: del self.main_window.plane_definitions[self.object_id]


class DeleteObjectCommand(ICommand):
    """Command to remove an existing object from the scene."""
    def __init__(self, main_window: 'MainWindow', obj_id: str):
        self.main_window = main_window
        self.obj_id = obj_id
        self.actor_to_delete = self.main_window.actor_buffer.get(self.obj_id)
        self.actor = self.actor_to_delete
        self.category: str | None = None
        self.type: str = "Unknown"
        self.plane_def = None
    def execute(self) -> None:
        if self.actor_to_delete:
            items = self.main_window.object_browser.findItems(self.obj_id, Qt.MatchExactly | Qt.MatchRecursive)
            if items:
                item = items[0]
                self.category = item.parent().text(0) if item.parent() else "Primitives"
                self.type = item.text(1)
            if self.obj_id in self.main_window.plane_definitions:
                self.plane_def = self.main_window.plane_definitions.pop(self.obj_id)
            self.main_window.renderer.RemoveActor(self.actor_to_delete)
            self.main_window.object_browser.remove_object(self.obj_id)
            if self.obj_id in self.main_window.actor_buffer:
                del self.main_window.actor_buffer[self.obj_id]
            self.main_window.logger.info(f"Deleted object: {self.obj_id}")
    def undo(self) -> None:
        if self.actor_to_delete and self.category:
            self.main_window.renderer.AddActor(self.actor_to_delete)
            self.main_window.object_browser.add_object(self.obj_id, self.type, self.category)
            self.main_window.actor_buffer[self.obj_id] = self.actor_to_delete
            if self.plane_def:
                self.main_window.plane_definitions[self.obj_id] = self.plane_def
            self.main_window.logger.info(f"Restored (Undo Delete): {self.obj_id}")


class RenameObjectCommand(ICommand):
    """Command to rename an object in the browser and all buffers."""
    def __init__(self, main_window: 'MainWindow', obj_id: str, new_name: str):
        self.main_window = main_window
        self.old_id = obj_id
        self.new_id = new_name
        self.actor = self.main_window.actor_buffer.get(self.old_id)
    def execute(self):
        self.main_window.object_browser.update_object_name(self.old_id, self.new_id)
        actor = self.main_window.actor_buffer.pop(self.old_id, None)
        if actor: self.main_window.actor_buffer[self.new_id] = actor
        plane_def = self.main_window.plane_definitions.pop(self.old_id, None)
        if plane_def: self.main_window.plane_definitions[self.new_id] = plane_def
        if self.main_window.active_plane_id == self.old_id: self.main_window.active_plane_id = self.new_id
        self.main_window.logger.info(f"Renamed '{self.old_id}' to '{self.new_id}'")
    def undo(self):
        self.main_window.object_browser.update_object_name(self.new_id, self.old_id)
        actor = self.main_window.actor_buffer.pop(self.new_id, None)
        if actor: self.main_window.actor_buffer[self.old_id] = actor
        plane_def = self.main_window.plane_definitions.pop(self.new_id, None)
        if plane_def: self.main_window.plane_definitions[self.old_id] = plane_def
        if self.main_window.active_plane_id == self.new_id: self.main_window.active_plane_id = self.old_id
        self.main_window.logger.info(f"Undo rename: '{self.new_id}' back to '{self.old_id}'")


class ToggleVisibilityCommand(ICommand):
    """Command to show or hide an actor."""
    def __init__(self, main_window: 'MainWindow', obj_id: str):
        self.main_window = main_window
        self.obj_id = obj_id
        self.actor = main_window.actor_buffer.get(obj_id)
        self.previous_visibility_state = self.actor.GetVisibility() if self.actor else 0
    def execute(self):
        if self.actor:
            new_visibility = 1 - self.actor.GetVisibility()
            self.actor.SetVisibility(new_visibility)
            self.main_window.logger.info(f"Set visibility for {self.obj_id} to {'ON' if new_visibility else 'OFF'}")
    def undo(self):
        if self.actor: self.actor.SetVisibility(self.previous_visibility_state)


class SetActivePlaneCommand(ICommand):
    """Command to change the active working plane state and highlighting."""
    def __init__(self, main_window: 'MainWindow', new_active_plane_id: str | None):
        self.main_window = main_window
        self.old_active_id = main_window.active_plane_id
        self.new_active_id = new_active_plane_id
        self.actor = self.main_window.actor_buffer.get(new_active_plane_id)
    def execute(self) -> None:
        if self.old_active_id and self.old_active_id in self.main_window.actor_buffer:
            actor = self.main_window.actor_buffer[self.old_active_id]
            actor.GetProperty().SetColor(0.8, 0.8, 1.0); actor.GetProperty().SetOpacity(0.2)
        if self.new_active_id and self.new_active_id in self.main_window.actor_buffer:
            new_actor = self.main_window.actor_buffer[self.new_active_id]
            new_actor.GetProperty().SetColor(0.0, 1.0, 1.0); new_actor.GetProperty().SetOpacity(0.4)
            plane_def = self.main_window.plane_definitions.get(self.new_active_id)
            if plane_def:
                self.main_window.update_plane_context(plane_def)
                self.main_window.active_plane_id = self.new_active_id
                self.main_window.object_browser.set_active_plane_id(self.new_active_id)
                self.main_window.logger.info(f"Active plane set to: {self.new_active_id}")
    def undo(self) -> None:
        redo_command = SetActivePlaneCommand(self.main_window, self.old_active_id)
        redo_command.old_active_id = self.new_active_id
        redo_command.execute()
        self.main_window.logger.info(f"Active plane reverted to: {self.old_active_id}")


class ImportDxfCommand(ICommand):
    """Command to import a DXF file as a grouped entity with a custom origin."""
    def __init__(self, main_window: 'MainWindow', filepath: str, origin: list, plane_context: dict):
        self.main_window = main_window
        self.filepath = filepath
        self.origin = origin
        self.plane_context = plane_context
        self.group_name = f"DXF_Import_{id(self)}"
        self.created_actors: Dict[str, vtk.vtkActor] = {}
        self.actor = True

    def execute(self) -> None:
        if self.created_actors:
            self.main_window.object_browser.add_object(self.group_name, "DXF Group", "Imports")
            for obj_id, actor in self.created_actors.items():
                self.main_window.renderer.AddActor(actor)
                self.main_window.actor_buffer[obj_id] = actor
                # The type is retrieved from the actor's stored properties if needed,
                # but for simplicity, we just re-add it.
                self.main_window.object_browser.add_object(obj_id, "Shape", "Imports", parent_id=self.group_name)
            return

        try:
            self.main_window.object_browser.add_object(self.group_name, "DXF Group", "Imports")

            # --- MODIFICATION: The entire block for creating the origin sphere has been removed. ---
            
            reader = DxfReader(self.filepath)
            geom_backend = reader.get_geometry()
            
            if geom_backend.get_number_of_shapes() == 0:
                self.main_window.logger.warning(f"No supported geometry (LINE, CIRCLE, LWPOLYLINE) found in '{self.filepath}'.")

            for i, shape in enumerate(geom_backend.shapes):
                poly_data = vtk.vtkPolyData()
                shape_type = shape.get_type()
                
                if shape_type in ("LINE", "CIRCLE", "ARC", "LWPOLYLINE"):
                    viz_data = None
                    if shape_type == "LINE":
                        p1, p2 = shape.start_point, shape.end_point
                        viz_data = primitives.create_line(p1[0],p1[1],p2[0],p2[1], self.plane_context)
                    elif shape_type in ("CIRCLE", "ARC"):
                        c, r = shape.center, shape.radius
                        viz_data = primitives.create_circle(c[0],c[1],r, self.plane_context)
                    elif shape_type == "LWPOLYLINE":
                        points = []
                        for v in shape.vertices:
                            points_3d = primitives.transform_to_plane(v[0], v[1], **self.plane_context)
                            points.append(points_3d)
                        viz_data = {'points': points, 'cells': [list(range(len(points)))], 'type': 'lines'}
                    if not viz_data: continue

                    vtk_points = vtk.vtkPoints()
                    for p in viz_data['points']: vtk_points.InsertNextPoint(p)
                    poly_data.SetPoints(vtk_points)

                    cell_array = vtk.vtkCellArray()
                    cell = vtk.vtkPolyLine()
                    cell.GetPointIds().SetNumberOfIds(len(viz_data['points']))
                    for pt_idx in range(len(viz_data['points'])):
                        cell.GetPointIds().SetId(pt_idx, pt_idx)
                    cell_array.InsertNextCell(cell)
                    poly_data.SetLines(cell_array)
                    
                    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly_data)
                    actor = vtk.vtkActor(); actor.SetMapper(mapper)
                    
                    # This is the crucial transformation step that is preserved.
                    actor.SetPosition(self.origin)
                    
                    actor.GetProperty().SetColor(1, 0.4, 0.4)
                    
                    obj_id = f"{self.group_name}_Shape_{i}"
                    self.created_actors[obj_id] = actor
                    self.main_window.object_browser.add_object(obj_id, shape_type, "Imports", parent_id=self.group_name)

            for obj_id, actor in self.created_actors.items():
                self.main_window.renderer.AddActor(actor)
                self.main_window.actor_buffer[obj_id] = actor

        except Exception as e:
            self.main_window.logger.error(f"DXF Import failed: {e}")
            self.actor = False

    def undo(self) -> None:
        """Removes the group from the browser and all its actors from the scene."""
        for obj_id, actor in self.created_actors.items():
            self.main_window.renderer.RemoveActor(actor)
            if obj_id in self.main_window.actor_buffer:
                del self.main_window.actor_buffer[obj_id]
        
        self.main_window.object_browser.remove_object(self.group_name)


class CreateCuboidCommand(ICommand):
    """Command to create a solid cuboid from various methods."""
    def __init__(self, main_window: 'MainWindow', creation_data: dict):
        self.main_window = main_window
        self.creation_data = creation_data
        self.actor: vtk.vtkActor | None = None
        self.object_id = f"Cuboid_{id(self)}"

    def execute(self) -> None:
        if self.actor:
            # Redo operation
            self.main_window.renderer.AddActor(self.actor)
            self.main_window.actor_buffer[self.object_id] = self.actor
            self.main_window.object_browser.add_object(self.object_id, "Cuboid", "Primitives")
            return
        
        try:
            method = self.creation_data["method"]
            if method == "dimensions":
                geom_data = primitives.create_cuboid_from_dimensions(
                    dimensions=self.creation_data["dimensions"],
                    center=self.creation_data["center"],
                    orientation=self.creation_data["orientation"]
                )
            elif method == "corners":
                geom_data = primitives.create_cuboid_from_corners(
                    p1=self.creation_data["p1"],
                    p2=self.creation_data["p2"]
                )
            else:
                raise ValueError(f"Unknown cuboid creation method: {method}")

            # Generic actor creation from geom_data
            vtk_points = vtk.vtkPoints()
            for p in geom_data['points']: vtk_points.InsertNextPoint(p)
            cell_array = vtk.vtkCellArray()
            for cell_indices in geom_data['cells']:
                cell = vtk.vtkPolygon()
                cell.GetPointIds().SetNumberOfIds(len(cell_indices))
                for i, point_id in enumerate(cell_indices):
                    cell.GetPointIds().SetId(i, point_id)
                cell_array.InsertNextCell(cell)
            
            poly_data = vtk.vtkPolyData()
            poly_data.SetPoints(vtk_points)
            poly_data.SetPolys(cell_array)

            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly_data)
            self.actor = vtk.vtkActor(); self.actor.SetMapper(mapper)
            self.actor.GetProperty().SetColor(0.9, 0.4, 0.1) # Orange color

            self.main_window.renderer.AddActor(self.actor)
            self.main_window.actor_buffer[self.object_id] = self.actor
            self.main_window.object_browser.add_object(self.object_id, "Cuboid", "Primitives")

        except Exception as e:
            self.main_window.logger.error(f"Failed to create cuboid: {e}")
            self.actor = None # Mark command as failed

    def undo(self) -> None:
        if self.actor:
            self.main_window.renderer.RemoveActor(self.actor)
            self.main_window.object_browser.remove_object(self.object_id)
            if self.object_id in self.main_window.actor_buffer:
                del self.main_window.actor_buffer[self.object_id]        