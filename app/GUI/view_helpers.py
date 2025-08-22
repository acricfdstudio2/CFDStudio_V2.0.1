"""A dedicated module to manage all VTK view and camera manipulations."""

import vtk
import numpy as np


class ViewManager:
    """
    Manages operations related to the VTK viewport, including camera
    positions, projections, and actor representation styles.
    """

    def __init__(self, renderer: vtk.vtkRenderer, render_window: vtk.vtkRenderWindow):
        self.renderer = renderer
        self.render_window = render_window
        self.camera = renderer.GetActiveCamera()

    def _set_view(self, position: tuple, view_up: tuple):
        """Generic helper to set a standard camera view."""
        try:
            bounds = self.renderer.ComputeVisiblePropBounds()
            # If no visible props, use a default view area
            if bounds[0] > bounds[1]:
                center = [0, 0, 0]
                distance = 100.0
            else:
                center = [(bounds[0] + bounds[1]) / 2.0,
                          (bounds[2] + bounds[3]) / 2.0,
                          (bounds[4] + bounds[5]) / 2.0]
                diag = np.sqrt((bounds[1]-bounds[0])**2 + (bounds[3]-bounds[2])**2 + (bounds[5]-bounds[4])**2)
                distance = diag * 2.0

            self.camera.SetFocalPoint(center)
            self.camera.SetPosition(center[0] + position[0] * distance,
                                    center[1] + position[1] * distance,
                                    center[2] + position[2] * distance)
            self.camera.SetViewUp(view_up)
            self.renderer.ResetCameraClippingRange()
            self.render_window.Render()
        except Exception as e:
            print(f"Error setting view: {e}")

    def set_top_view(self): self._set_view(position=(0, 0, 1), view_up=(0, 1, 0))
    def set_bottom_view(self): self._set_view(position=(0, 0, -1), view_up=(0, 1, 0))
    def set_front_view(self): self._set_view(position=(0, -1, 0), view_up=(0, 0, 1))
    def set_back_view(self): self._set_view(position=(0, 1, 0), view_up=(0, 0, 1))
    def set_left_view(self): self._set_view(position=(-1, 0, 0), view_up=(0, 0, 1))
    def set_right_view(self): self._set_view(position=(1, 0, 0), view_up=(0, 0, 1))
    def set_iso_view(self): self._set_view(position=(1, 1, 1), view_up=(0, 0, 1))

    def reset_view(self):
        self.renderer.ResetCamera()
        self.render_window.Render()

    def set_projection_perspective(self):
        self.camera.ParallelProjectionOff()
        self.render_window.Render()

    def set_projection_orthogonal(self):
        self.camera.ParallelProjectionOn()
        self.render_window.Render()

    def _set_all_actors_representation(self, representation_type: int):
        """Helper to set representation style, ignoring special objects like planes."""
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextActor()
        main_window = self.render_window.GetInteractor().GetInteractorStyle().main_window

        while actor:
            # Avoid changing the visual style of working planes
            if not main_window.is_actor_a_plane(actor):
                 actor.GetProperty().SetRepresentation(representation_type)
            actor = actors.GetNextActor()
        self.render_window.Render()

    def set_representation_surface(self): self._set_all_actors_representation(vtk.VTK_SURFACE)
    def set_representation_wireframe(self): self._set_all_actors_representation(vtk.VTK_WIREFRAME)

    def set_representation_surface_with_edges(self):
        """Shows a solid surface with black edges highlighted."""
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextActor()
        main_window = self.render_window.GetInteractor().GetInteractorStyle().main_window

        while actor:
            if not main_window.is_actor_a_plane(actor):
                prop = actor.GetProperty()
                prop.SetRepresentationToSurface()
                prop.EdgeVisibilityOn()
                prop.SetEdgeColor(0, 0, 0)
            actor = actors.GetNextActor()
        self.render_window.Render()