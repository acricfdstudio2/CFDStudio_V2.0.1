# File: app/GUI/interaction.py
"""This module defines the custom VTK interactor style for the application."""

from typing import TYPE_CHECKING
import vtk
# MODIFICATION: QObject and pyqtSignal are no longer needed here.

if TYPE_CHECKING:
    from .main_window import MainWindow

# MODIFICATION: Removed QObject from inheritance list.
class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """A mode-aware interactor for navigation and selection."""
    # MODIFICATION: The signal is removed.
    # pointPicked = pyqtSignal(list)

    def __init__(self, main_window: 'MainWindow'):
        # MODIFICATION: QObject.__init__ is removed.
        super().__init__()
        self.main_window = main_window
        self.logger = main_window.logger
        self.last_picked_actor: vtk.vtkActor | None = None
        self.last_picked_property: vtk.vtkProperty = vtk.vtkProperty()
        self.mode = "navigation"

        self.cell_picker = vtk.vtkCellPicker()
        self.point_picker = vtk.vtkPointPicker()
        self.point_picker.SetUseCells(True)

        self.surface_highlighter_actor = vtk.vtkActor()
        prop = self.surface_highlighter_actor.GetProperty()
        prop.SetColor(1.0, 1.0, 0.0); prop.SetOpacity(0.5); prop.SetLighting(False)

        self.pickable_points_actor = vtk.vtkActor()
        self.hover_point_actor = vtk.vtkActor()
        
        self.AddObserver("LeftButtonPressEvent", self._on_left_button_press)
        self.AddObserver("MouseMoveEvent", self._on_mouse_move)

    def _on_left_button_press(self, obj, event):
        """Handles left-click for all modes."""
        if self.mode == "surface_selection":
            self._finalize_surface_pick()
            return

        elif self.mode == "point_selection":
            if self.point_picker.GetPointId() >= 0:
                picked_pos = self.point_picker.GetPickPosition()
                self.logger.info(f"Point picked at coordinates: {picked_pos}")
                # MODIFICATION: Directly call a method on MainWindow instead of emitting a signal.
                self.main_window.on_point_picked(list(picked_pos))
                self.set_mode("navigation")
            else:
                self.logger.warning("Point pick failed: Clicked on empty space.")
                self.set_mode("navigation")
            return
            
        elif self.mode == "navigation":
            # ... (navigation logic is unchanged)
            click_pos = self.GetInteractor().GetEventPosition()
            picker = vtk.vtkPicker()
            picker.Pick(click_pos[0], click_pos[1], 0, self.main_window.renderer)
            if self.last_picked_actor:
                self.last_picked_actor.GetProperty().DeepCopy(self.last_picked_property)
            self.last_picked_actor = picker.GetActor()
            if self.last_picked_actor:
                self.last_picked_property.DeepCopy(self.last_picked_actor.GetProperty())
                self.last_picked_actor.GetProperty().SetColor(1.0, 0.0, 0.0)
                obj_id = self.main_window.get_id_from_actor(self.last_picked_actor)
                self.logger.info(f"Selected actor: {obj_id or 'Unknown'}")
            else:
                self.logger.info("Deselected all.")
        
        self.OnLeftButtonDown()
        self.main_window.vtkWidget.GetRenderWindow().Render()

    # ... The rest of the file (set_mode, start_point_picking, etc.) remains exactly the same.
    def set_mode(self, mode: str):
        self.mode = mode
        self.logger.info(f"Interactor mode switched to: {self.mode}")
        if self.mode != "surface_selection": self._remove_surface_highlighter()
        if self.mode != "point_selection": self._stop_point_picking()
        self.main_window.vtkWidget.GetRenderWindow().Render()
    def start_point_picking(self):
        self.set_mode("point_selection")
        all_points = vtk.vtkPoints()
        for actor in self.main_window.actor_buffer.values():
            if not actor.GetMapper() or not actor.GetMapper().GetInput(): continue
            polydata = actor.GetMapper().GetInput()
            for i in range(polydata.GetNumberOfPoints()): all_points.InsertNextPoint(polydata.GetPoint(i))
        if all_points.GetNumberOfPoints() == 0:
            self.logger.warning("Point picking started, but no vertices found in scene.")
            return
        polydata = vtk.vtkPolyData(); polydata.SetPoints(all_points)
        sphere = vtk.vtkSphereSource(); sphere.SetRadius(0.1)
        glyph = vtk.vtkGlyph3D(); glyph.SetSourceConnection(sphere.GetOutputPort()); glyph.SetInputData(polydata)
        mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(glyph.GetOutputPort())
        self.pickable_points_actor.SetMapper(mapper)
        self.pickable_points_actor.GetProperty().SetColor(0.7, 0.7, 0.7)
        self.main_window.renderer.AddActor(self.pickable_points_actor)
        hover_sphere = vtk.vtkSphereSource(); hover_sphere.SetRadius(0.2)
        hover_mapper = vtk.vtkPolyDataMapper(); hover_mapper.SetInputConnection(hover_sphere.GetOutputPort())
        self.hover_point_actor.SetMapper(hover_mapper)
        self.hover_point_actor.GetProperty().SetColor(1.0, 1.0, 0.0)
        self.main_window.vtkWidget.GetRenderWindow().Render()
    def _stop_point_picking(self):
        if self.main_window.renderer.HasViewProp(self.pickable_points_actor):
            self.main_window.renderer.RemoveActor(self.pickable_points_actor)
        if self.main_window.renderer.HasViewProp(self.hover_point_actor):
            self.main_window.renderer.RemoveActor(self.hover_point_actor)
    def _update_point_hover(self):
        click_pos = self.GetInteractor().GetEventPosition()
        self.point_picker.Pick(click_pos[0], click_pos[1], 0, self.main_window.renderer)
        if self.point_picker.GetPointId() >= 0:
            picked_pos = self.point_picker.GetPickPosition()
            self.hover_point_actor.SetPosition(picked_pos)
            if not self.main_window.renderer.HasViewProp(self.hover_point_actor):
                self.main_window.renderer.AddActor(self.hover_point_actor)
        else:
            if self.main_window.renderer.HasViewProp(self.hover_point_actor):
                self.main_window.renderer.RemoveActor(self.hover_point_actor)
        self.main_window.vtkWidget.GetRenderWindow().Render()
    def _on_mouse_move(self, obj, event):
        if self.mode == "surface_selection":
            click_pos = self.GetInteractor().GetEventPosition()
            self.cell_picker.Pick(click_pos[0], click_pos[1], 0, self.main_window.renderer)
            if self.main_window.is_actor_a_plane(self.cell_picker.GetActor()) or self.cell_picker.GetCellId() < 0:
                self._remove_surface_highlighter()
            else:
                self._update_surface_highlighter()
            self.main_window.vtkWidget.GetRenderWindow().Render()
        elif self.mode == "point_selection":
            self._update_point_hover()
        self.OnMouseMove()
    def _finalize_surface_pick(self):
        picked_actor = self.cell_picker.GetActor()
        if self.cell_picker.GetCellId() >= 0 and not self.main_window.is_actor_a_plane(picked_actor):
            self.logger.info("Surface clicked! Finalizing selection...")
            picked_dataset = self.cell_picker.GetDataSet()
            picked_cell_id = self.cell_picker.GetCellId()
            if picked_dataset and picked_cell_id >= 0:
                picked_cell = picked_dataset.GetCell(picked_cell_id)
                bounds = picked_cell.GetBounds()
                origin = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]
                normal = [0.0, 0.0, 0.0]
                vtk.vtkPolygon.ComputeNormal(picked_cell.GetPoints(), normal)
                self.main_window.finalize_surface_selection(origin, normal)
            self.set_mode("navigation")
        else:
            self.logger.info("Clicked on empty space or a plane. Exiting selection mode.")
            self.set_mode("navigation")
    def _update_surface_highlighter(self):
        picked_actor = self.cell_picker.GetActor()
        picked_cell_id = self.cell_picker.GetCellId()
        if not picked_actor or picked_cell_id < 0: return
        full_polydata = picked_actor.GetMapper().GetInput()
        cell_id_list = vtk.vtkIdList(); cell_id_list.InsertNextId(picked_cell_id)
        extractor = vtk.vtkExtractCells(); extractor.SetInputData(full_polydata); extractor.SetCellList(cell_id_list); extractor.Update()
        mapper = vtk.vtkDataSetMapper(); mapper.SetInputConnection(extractor.GetOutputPort())
        self.surface_highlighter_actor.SetMapper(mapper)
        if not self.main_window.renderer.HasViewProp(self.surface_highlighter_actor):
            self.main_window.renderer.AddActor(self.surface_highlighter_actor)
    def _remove_surface_highlighter(self):
        if self.main_window.renderer.HasViewProp(self.surface_highlighter_actor):
            self.main_window.renderer.RemoveActor(self.surface_highlighter_actor)