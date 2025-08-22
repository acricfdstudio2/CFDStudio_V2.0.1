# File: app/GUI/main_window.py
"""The main application window, orchestrating all UI and backend logic."""

import logging
from typing import Any, Dict, List

import numpy as np
import vtk
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import (QDockWidget, QFileDialog, QInputDialog,
                             QMainWindow, QMessageBox, QTabBar, QTextEdit)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util import numpy_support as vtk_numpy_support

from acrilib.primitives import factory as primitives
from acrilib.readers.dxf_reader import DxfReader
from acrilib.threed import ThreeDMenu
from acrilib.threed.coords import CoordinateSystemManager
from . import dialogs
from .commands import (ICommand, CreateObjectCommand, CreateCuboidCommand,
                       DeleteObjectCommand, ImportDxfCommand,
                       RenameObjectCommand, SetActivePlaneCommand,
                       ToggleVisibilityCommand)
from .interaction import CustomInteractorStyle
from .menu_manager import MenuManager
from .view_helpers import ViewManager
from .widgets import QtLogHandler, ObjectBrowser


class MainWindow(QMainWindow):
    """The main application window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACRI-CAD Development Environment")
        self.setGeometry(50, 50, 1600, 1000)

        # --- Core Application State ---
        self.command_stack: List[ICommand] = []
        self.stack_pointer: int = -1
        self.actor_buffer: Dict[str, vtk.vtkActor] = {}
        self.plane_definitions: Dict[str, Dict] = {}
        self.active_plane_id: str | None = None
        self.current_plane_origin: List[float] = [0, 0, 0]
        self.current_plane_u_axis: List[float] = [1, 0, 0]
        self.current_plane_v_axis: List[float] = [0, 1, 0]
        self.point_pick_target_widget = None

        # --- Backend Logic ---
        self.threed_menu_backend = ThreeDMenu()
        self.cs_manager = CoordinateSystemManager()

        # --- VTK and UI Setup ---
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.setCentralWidget(self.vtkWidget)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self._create_dock_windows()
        self._setup_logging()

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactor_style = CustomInteractorStyle(self)
        self.interactor.SetInteractorStyle(self.interactor_style)

        self.view_manager = ViewManager(self.renderer, self.vtkWidget.GetRenderWindow())
        self.menu_manager = MenuManager(self)
        self.menu_manager.build_menus("menu.json")

        self._connect_signals()
        self.on_plane_reset_xy(is_initial_setup=True)
        self.object_browser.add_object("Global", "LCS", "Coordinate Systems")
        self.interactor.Initialize()
        self.logger.info("Application initialized successfully.")
        self.logger.info(f"Active System: {self.cs_manager.active_cs_title}")

    def closeEvent(self, event):
        """
        Gracefully handle application shutdown.
        This is the crucial fix for the RuntimeError.
        """
        logger = logging.getLogger("CADApp")
        # Find our specific handler and remove it from the logging system
        for handler in logger.handlers[:]:
            if isinstance(handler, QtLogHandler):
                logger.removeHandler(handler)
        
        # Proceed with the normal closing process
        event.accept()
        super().closeEvent(event)

    def _create_dock_windows(self) -> None:
        self.docks = {}
        self.object_browser = ObjectBrowser(self)
        self.command_window = QTextEdit("# Enter commands here...")
        self.status_window = QTextEdit(); self.status_window.setReadOnly(True)
        self.error_window = QTextEdit(); self.error_window.setReadOnly(True)
        self.python_console = QTextEdit(">>> "); self.python_console.setFont(QFont("Courier New", 10))
        self.properties_inspector = QTextEdit("--- Properties ---"); self.properties_inspector.setReadOnly(True)
        dock_data = {
            "Object Browser": (self.object_browser, Qt.LeftDockWidgetArea),
            "Command Window": (self.command_window, Qt.LeftDockWidgetArea),
            "Properties": (self.properties_inspector, Qt.RightDockWidgetArea),
            "Status Window": (self.status_window, Qt.BottomDockWidgetArea),
            "Error Window": (self.error_window, Qt.BottomDockWidgetArea),
            "Python Console": (self.python_console, Qt.BottomDockWidgetArea),
        }
        for name, (widget, area) in dock_data.items():
            dock = QDockWidget(name, self)
            dock.setWidget(widget)
            self.addDockWidget(area, dock)
            self.docks[name] = dock
        self.splitDockWidget(self.docks["Object Browser"], self.docks["Command Window"], Qt.Vertical)
        self.tabifyDockWidget(self.docks["Status Window"], self.docks["Error Window"])
        self.tabifyDockWidget(self.docks["Error Window"], self.docks["Python Console"])
        self.docks["Status Window"].raise_()
        self._connect_tab_signals()

    def _connect_tab_signals(self):
        self.bottom_tab_bar = None
        for tab_bar in self.findChildren(QTabBar):
            tab_texts = [tab_bar.tabText(i) for i in range(tab_bar.count())]
            if "Error Window" in tab_texts and "Status Window" in tab_texts:
                self.bottom_tab_bar = tab_bar
                break
        if self.bottom_tab_bar:
            self.bottom_tab_bar.tabBarClicked.connect(self._clear_error_notification)
        else:
            logging.warning("Could not find the bottom tab bar to connect error notification signals.")

    def _setup_logging(self) -> None:
        self.logger = logging.getLogger("CADApp")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = QtLogHandler(self)
            handler.log_record_emitted.connect(self.route_log_message)
            self.logger.addHandler(handler)

    def route_log_message(self, record: logging.LogRecord):
        msg = self.logger.handlers[0].formatter.format(record)
        if record.levelno >= logging.WARNING:
            self.error_window.append(msg)
            self._notify_error_tab()
        else:
            self.status_window.append(msg)

    def _notify_error_tab(self):
        if not self.bottom_tab_bar: return
        for i in range(self.bottom_tab_bar.count()):
            if self.bottom_tab_bar.tabText(i) in ["Error Window", "Error 🔴"]:
                self.bottom_tab_bar.setTabText(i, "Error 🔴")
                self.bottom_tab_bar.setTabTextColor(i, Qt.red)
                return

    def _clear_error_notification(self, index: int):
        if not self.bottom_tab_bar: return
        if self.bottom_tab_bar.tabText(index) == "Error 🔴":
            self.bottom_tab_bar.setTabText(index, "Error Window")
            self.bottom_tab_bar.setTabTextColor(index, Qt.black)

    def _connect_signals(self) -> None:
        self.object_browser.object_delete_requested.connect(self.on_delete_object_requested)
        self.object_browser.object_rename_requested.connect(self.on_rename_object_requested)
        self.object_browser.object_visibility_toggled.connect(self.on_visibility_toggle_requested)
        self.object_browser.object_set_active_requested.connect(self.on_set_active_cs_requested)

    def execute_command(self, command: ICommand) -> None:
        try:
            if self.stack_pointer < len(self.command_stack) - 1:
                self.command_stack = self.command_stack[:self.stack_pointer + 1]
            command.execute()
            if not getattr(command, 'actor', True):
                self.logger.error(f"Command {command.__class__.__name__} failed execution.")
                return
            self.command_stack.append(command)
            self.stack_pointer += 1
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
        except Exception as e:
            self.logger.error(f"Failed to execute command {command.__class__.__name__}: {e}")

    def handle_action(self, action_id: str) -> None:
        handler = getattr(self, f"on_{action_id}", lambda: self.placeholder_function(action_id))
        handler()

    def placeholder_function(self, feature_name: str) -> None:
        self.logger.info(f"User clicked placeholder: {feature_name}")
        QMessageBox.information(self, "Not Implemented", f"The '{feature_name}' feature is a placeholder.")

    def on_new_project(self) -> None:
        reply = QMessageBox.question(self, "New Project", "Start a new project?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logger.info("Starting new project. Clearing all data.")
            self.cs_manager.reset()
            self.renderer.RemoveAllViewProps()
            self.actor_buffer.clear()
            self.plane_definitions.clear()
            self.command_stack.clear()
            self.stack_pointer = -1
            self.object_browser.clear()
            self.object_browser.add_object("Global", "LCS", "Coordinate Systems")
            self.on_plane_reset_xy(is_initial_setup=True)
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
            self.logger.info("Scene cleared. Ready for new project.")

    def on_import_dxf(self) -> None:
        dialog = dialogs.DxfImportDialog(self._get_existing_plane_ids(), self)
        # Connect the dialog's pick request to the main window's handler
        dialog.origin_widget.pickFromScreenRequested.connect(lambda: self.start_point_picking_mode(dialog.origin_widget))
        
        if dialog.exec_() and dialog.result_data:
            data = dialog.result_data
            plane_context = self._get_plane_context_from_selection(data['plane_context'])
            if not plane_context:
                self.logger.error("Failed to resolve plane context for DXF import.")
                return
            cmd = ImportDxfCommand(main_window=self, filepath=data['filepath'], origin=data['origin'], plane_context=plane_context)
            self.execute_command(cmd)
            self.logger.info(f"Successfully started import of '{data['filepath']}'.")
        self.point_pick_target_widget = None

    def on_import_vtk(self) -> None:
        fp, _ = QFileDialog.getOpenFileName(self, "Open VTK File", "", "VTK Files (*.vtk *.vtp *.vtu);;All Files (*)")
        if not fp: return
        try:
            reader = vtk.vtkGenericDataObjectReader()
            reader.SetFileName(fp)
            reader.Update()
            if not reader.GetOutput() or reader.GetOutput().GetNumberOfPoints() == 0:
                self.logger.warning(f"VTK reader found no geometry in '{fp}'.")
                return
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.8, 0.8, 0.2)
            geom_data = {'type': 'VTK Import', 'actor': actor}
            self.execute_command(CreateObjectCommand(self, geom_data, category="Imports"))
            self.logger.info(f"Imported VTK file: '{fp}'")
        except Exception as e:
            self.logger.error(f"Failed to import VTK file: {e}")

    def on_print_view(self) -> None:
        try:
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                painter = QPainter(printer)
                w2if = vtk.vtkWindowToImageFilter()
                w2if.SetInput(self.vtkWidget.GetRenderWindow())
                w2if.Update()
                img_data = w2if.GetOutput()
                w,h,_ = img_data.GetDimensions()
                vtk_array = img_data.GetPointData().GetScalars()
                c = vtk_array.GetNumberOfComponents()
                numpy_img = vtk_numpy_support.vtk_to_numpy(vtk_array).reshape(h, w, c)
                q_image = QImage(numpy_img.data, w, h, w * c, QImage.Format_RGB888).rgbSwapped().mirrored(False, True)
                rect = painter.viewport()
                size = q_image.size()
                size.scale(rect.size(), Qt.KeepAspectRatio)
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(q_image.rect())
                painter.drawImage(0, 0, q_image)
                painter.end()
                self.logger.info("View sent to printer.")
        except Exception as e:
            self.logger.error(f"Printing failed: {e}")

    def on_exit_app(self): self.close()

    def on_undo(self):
        if self.stack_pointer >= 0:
            cmd = self.command_stack[self.stack_pointer]
            cmd.undo()
            self.stack_pointer -= 1
            self.logger.info(f"Undo: {cmd.__class__.__name__}")
            self.vtkWidget.GetRenderWindow().Render()
        else:
            self.logger.warning("Nothing to undo.")

    def on_redo(self):
        if self.stack_pointer < len(self.command_stack) - 1:
            self.stack_pointer += 1
            cmd = self.command_stack[self.stack_pointer]
            cmd.execute()
            self.logger.info(f"Redo: {cmd.__class__.__name__}")
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
        else:
            self.logger.warning("Nothing to redo.")

    def on_delete_object(self): self.on_delete_selected_from_menu()

    def on_delete_selected_from_menu(self):
        selected_actor = getattr(self.interactor_style, 'last_picked_actor', None)
        if not selected_actor:
            QMessageBox.information(self, "Delete Object", "No object selected.")
            return
        obj_id = self.get_id_from_actor(selected_actor)
        if obj_id:
            self.on_delete_object_requested(obj_id)
        else:
            self.logger.error("Selected actor not found in actor buffer.")

    def on_view_top(self): self.view_manager.set_top_view()
    def on_view_bottom(self): self.view_manager.set_bottom_view()
    def on_view_front(self): self.view_manager.set_front_view()
    def on_view_back(self): self.view_manager.set_back_view()
    def on_view_left(self): self.view_manager.set_left_view()
    def on_view_right(self): self.view_manager.set_right_view()
    def on_view_iso(self): self.view_manager.set_iso_view()
    def on_reset_view(self): self.view_manager.reset_view()
    def on_proj_persp(self): self.view_manager.set_projection_perspective()
    def on_proj_ortho(self): self.view_manager.set_projection_orthogonal()
    def on_view_surf(self): self.view_manager.set_representation_surface()
    def on_view_surf_edge(self): self.view_manager.set_representation_surface_with_edges()
    def on_view_wire(self): self.view_manager.set_representation_wireframe()

    def on_plane_from_input(self):
        dialog = dialogs.PlaneCreationDialog(self)
        if dialog.exec_() and dialog.result_data:
            plane_name = dialog.result_data.get('name')
            if plane_name in self.actor_buffer:
                QMessageBox.critical(self, "Name Conflict", f"An object named '{plane_name}' already exists.")
                return
            self.on_plane_data_received(dialog.result_data)

    def on_plane_from_lcs(self):
        cs_keys = list(self.cs_manager.systems.keys())
        if not cs_keys:
            QMessageBox.information(self, "No Systems", "No Local Coordinate Systems have been created.")
            return
        cs_display_list = [f"{title} - {self.cs_manager.systems[title]}" for title in cs_keys]
        item, ok = QInputDialog.getItem(self, "Select Coordinate System", "Select a CS:", cs_display_list, 0, False)
        if not ok or not item: return
        cs_title = item.split(' - ')[0]
        lcs = self.cs_manager.get_cs(cs_title)
        if not lcs:
            self.logger.error(f"Could not retrieve LCS with title '{cs_title}'.")
            return
        plane_types = ["OXY (Normal: Z)", "OYZ (Normal: X)", "OZX (Normal: Y)"]
        plane_type, ok = QInputDialog.getItem(self, "Select Plane", "Select a plane from the LCS:", plane_types, 0, False)
        if not ok or not plane_type: return
        origin = lcs.origin
        if "OXY" in plane_type: normal, name_suffix = lcs.z_axis, "OXY"
        elif "OYZ" in plane_type: normal, name_suffix = lcs.x_axis, "OYZ"
        else: normal, name_suffix = lcs.y_axis, "OZX"
        plane_name = f"Plane_from_{lcs.title}_{name_suffix}"
        if plane_name in self.actor_buffer:
            QMessageBox.warning(self, "Name Conflict", f"A plane named '{plane_name}' already exists.")
            return
        plane_data = {'method': 'point_vector', 'origin': origin, 'normal': normal, 'name': plane_name}
        self.on_plane_data_received(plane_data)

    def on_plane_from_surface(self): self.interactor_style.set_mode("surface_selection")

    def on_plane_reset_xy(self, is_initial_setup=False):
        name = "Global_XY_Plane"
        if is_initial_setup and name in self.actor_buffer: return
        self.on_plane_data_received({'method': 'reset', 'name': name}, is_initial_setup)

    def on_plane_data_received(self, data: dict, is_initial_setup=False):
        try:
            origin, normal = None, None
            method = data.get('method')
            if method == 'point_vector':
                origin, normal = np.array(data['origin']), np.array(data['normal'])
            elif method == 'three_points':
                p1,p2,p3 = np.array(data['p1']), np.array(data['p2']), np.array(data['p3'])
                origin, normal = p1, np.cross(p2-p1, p3-p1)
            elif method == 'reset':
                origin, normal = np.array([0,0,0]), np.array([0,0,1])
            if np.linalg.norm(normal) < 1e-6:
                self.logger.error("Cannot define plane: normal is a zero vector.")
                return
            normal /= np.linalg.norm(normal)
            plane_geom = primitives.create_plane_geometry_data(origin.tolist(), normal.tolist())
            plane_name = data.get('name', f"Plane_{id(plane_geom)}")
            create_cmd = CreateObjectCommand(self, plane_geom, category="Planes", color=(0.8, 0.8, 1.0), opacity=0.2, representation='wireframe', object_name=plane_name)
            set_active_cmd = SetActivePlaneCommand(self, create_cmd.object_id)
            if is_initial_setup:
                create_cmd.execute(); set_active_cmd.execute()
                self.command_stack.clear(); self.stack_pointer = -1
            else:
                self.execute_command(create_cmd); self.execute_command(set_active_cmd)
            self.logger.info(f"Plane '{create_cmd.object_id}' created and set as active.")
        except Exception as e:
            self.logger.error(f"Could not process plane data: {e}")

    def finalize_surface_selection(self, origin: List[float], normal: List[float]):
        self.logger.info(f"Surface selected. Defining new plane with origin {origin} and normal {normal}.")
        name = f"Plane_from_Surface_{id(origin)}"
        self.on_plane_data_received({'method': 'point_vector', 'origin': origin, 'normal': normal, 'name': name})

    def on_create_lcs(self):
        i = 1
        while f"LCS_{i}" in self.cs_manager.systems: i += 1
        default_title = f"LCS_{i}"
        dialog = dialogs.CoordinateSystemCreatorDialog(default_title, self)
        dialog.selectionRequested.connect(self.handle_point_selection_for_lcs)
        dialog.coordinateSystemCreated.connect(self.handle_cs_creation)
        dialog.exec()

    def handle_point_selection_for_lcs(self, target_widget: dialogs.PointInputWidget):
        self.logger.info("Selection requested for LCS dialog. Simulating user pick...")
        text, ok = QInputDialog.getText(self, "Simulate Point Selection", "Enter coords (e.g., '10, 20, 5'):")
        if ok and text:
            try:
                coords = tuple(map(float, text.split(',')))
                if len(coords) == 3:
                    target_widget.set_point(coords)
                    self.logger.info(f"Point {coords} selected and set in dialog.")
                else:
                    self.logger.warning("Invalid input. Provide 3 comma-separated numbers.")
            except (ValueError, TypeError):
                self.logger.error("Invalid format for coordinates.")

    def handle_cs_creation(self, method: str, data: dict):
        cs_title = data['title']
        self.logger.info(f"Attempting to create CS (Title: '{cs_title}') via '{method}' method.")
        try:
            if method == "3_points":
                new_cs = self.cs_manager.create_cs_from_3_points(title=cs_title, origin=data['origin'], point_on_x=data['point_on_x'], point_in_xy=data['point_in_xy'])
            elif method == "origin_vectors":
                new_cs = self.cs_manager.create_cs_from_vectors(title=cs_title, origin=data['origin'], x_dir=data['x_dir'], y_dir=data['y_dir'])
            else: raise ValueError(f"Unknown creation method: {method}")
            self.logger.info(f"Successfully created: {new_cs}")
            self.object_browser.add_object(cs_title, "LCS", "Coordinate Systems")
            if data['set_active']:
                self.cs_manager.set_active(cs_title)
                self.logger.info(f"System '{cs_title}' is now the active coordinate system.")
                self.object_browser.set_active_cs_title(cs_title)
        except ValueError as e:
            QMessageBox.critical(self, "LCS Creation Error", str(e))
            self.logger.error(f"LCS Creation Failed: {e}")

    def on_create_point(self): self._create_primitive(dialogs.PointDialog, primitives.create_point, "Point", color=(1,0,0), point_size=15)
    def on_create_line(self): self._create_primitive(dialogs.LineDialog, primitives.create_line, "Line", color=(0,1,0))
    def on_create_circle(self): self._create_primitive(dialogs.CircleDialog, primitives.create_circle, "Circle", color=(1,1,0))
    def on_create_triangle(self): self._create_primitive(dialogs.TriangleDialog, primitives.create_triangle, "Triangle", color=(0,0,1))
    def on_create_cuboid(self): self._create_primitive(dialogs.CuboidDialog, primitives.create_cuboid, "Cuboid", color=(1,0.5,0))
    def on_create_cube(self): self._create_primitive(dialogs.CubeDialog, primitives.create_cube_data, "Cube", color=(0.8,0.2,0.8))
    def on_create_sphere(self): self._create_primitive(dialogs.SphereDialog, primitives.create_sphere_data, "Sphere", color=(0.2,0.8,0.8))
    def on_create_cylinder(self): self._create_primitive(dialogs.CylinderDialog, primitives.create_cylinder_data, "Cylinder", color=(0.8,0.8,0.2))
    def on_create_cone(self): self._create_primitive(dialogs.ConeDialog, primitives.create_cone_data, "Cone", color=(0.2,0.4,0.8))
    
    def start_point_picking_mode(self, target_widget: dialogs.PointInputWidget):
        """Activates point picking mode and remembers which widget to update."""
        self.logger.info("Activating point picking mode...")
        self.point_pick_target_widget = target_widget
        self.interactor_style.start_point_picking()
    def on_point_picked(self, point: list):
        """This is the handler called directly by the interactor style."""
        if self.point_pick_target_widget:
            self.point_pick_target_widget.set_point(point)
            self.point_pick_target_widget = None
        else:
            self.logger.warning("A point was picked, but no target widget was registered to receive it.")

    def on_create_solid_cuboid(self):
        """Handles the creation of a solid cuboid using the new advanced dialog."""
        dialog = dialogs.CuboidCreationDialog(self._get_existing_plane_ids(), self)
        
        if not dialog.exec_() or not dialog.result_data:
            return

        data = dialog.result_data
        
        if data["method"] == "dimensions":
            plane_context = self._get_plane_context_from_selection(data["plane_selection"])
            if not plane_context:
                self.logger.error("Could not resolve plane for cuboid orientation.")
                return
            u = np.array(plane_context['u_axis'])
            v = np.array(plane_context['v_axis'])
            w = np.cross(u, v)
            data["orientation"] = {"u_axis": u.tolist(), "v_axis": v.tolist(), "w_axis": w.tolist()}
        
        cmd = CreateCuboidCommand(self, data)
        self.execute_command(cmd)

    def _create_primitive(self, dialog_class, factory_func, name, **kwargs):
        dialog = dialog_class(f"Create {name}", self._get_existing_plane_ids(), self)
        if dialog.exec_():
            plane_context = self._get_plane_context_from_selection(dialog.plane_context)
            if plane_context:
                geom = factory_func(*dialog.params, plane_context)
                self.execute_command(CreateObjectCommand(self, geom, category="Primitives", **kwargs))
                self.logger.info(f"{name} created.")

    def on_panel_object(self): self.docks["Object Browser"].toggleViewAction().trigger()
    def on_panel_command(self): self.docks["Command Window"].toggleViewAction().trigger()
    def on_panel_status(self): self.docks["Status Window"].toggleViewAction().trigger()
    def on_panel_error(self): self.docks["Error Window"].toggleViewAction().trigger()
    def on_panel_python(self): self.docks["Python Console"].toggleViewAction().trigger()

    def on_delete_object_requested(self, obj_id: str, category: str):
        if category == "Coordinate Systems":
            if self.cs_manager.delete_cs(obj_id):
                self.object_browser.remove_object(obj_id)
                self.logger.info(f"Deleted Coordinate System: '{obj_id}'")
            else:
                self.logger.error(f"Could not find LCS '{obj_id}' to delete.")
            return
        if obj_id == self.active_plane_id:
            QMessageBox.warning(self, "Action Denied", "Cannot delete the active working plane.")
            return
        if obj_id in self.actor_buffer:
            self.execute_command(DeleteObjectCommand(self, obj_id))
        else:
            self.logger.error(f"Could not find object '{obj_id}' to delete.")

    def on_rename_object_requested(self, obj_id: str, category: str):
        if category == "Coordinate Systems":
            new_title, ok = QInputDialog.getText(self, "Rename Coordinate System", "Enter new title:", text=obj_id)
            if ok and new_title and new_title != obj_id:
                try:
                    self.cs_manager.rename_cs(obj_id, new_title)
                    self.object_browser.update_object_name(obj_id, new_title)
                    if self.object_browser.active_cs_title == obj_id:
                        self.object_browser.set_active_cs_title(new_title)
                    self.logger.info(f"Renamed CS '{obj_id}' to '{new_title}'")
                except ValueError as e:
                    QMessageBox.warning(self, "Rename Failed", str(e))
            return
        new_name, ok = QInputDialog.getText(self, "Rename Object", "Enter new name:", text=obj_id)
        if ok and new_name and new_name != obj_id:
            if new_name in self.actor_buffer:
                QMessageBox.warning(self, "Rename Failed", "An object with this name already exists.")
                return
            self.execute_command(RenameObjectCommand(self, obj_id, new_name))

    def on_set_active_cs_requested(self, title: str):
        try:
            self.cs_manager.set_active(title)
            self.object_browser.set_active_cs_title(title)
            self.logger.info(f"Active coordinate system set to: '{title}'")
        except ValueError as e:
            self.logger.error(f"Failed to set active CS: {e}")

    def on_visibility_toggle_requested(self, obj_id: str):
        if obj_id in self.actor_buffer:
            command = ToggleVisibilityCommand(self, obj_id)
            self.execute_command(command)
        else:
            self.logger.warning(f"Visibility toggle requested for non-existent object ID: '{obj_id}'")

    def _get_existing_plane_ids(self) -> List[str]:
        return list(self.plane_definitions.keys())

    def _get_plane_context_from_selection(self, selection: Any) -> Dict | None:
        if selection is None: return None
        if selection == "active":
            return {'origin': self.current_plane_origin, 'u_axis': self.current_plane_u_axis, 'v_axis': self.current_plane_v_axis}
        if isinstance(selection, str):
            plane_def = self.plane_definitions.get(selection)
            if plane_def:
                u_axis, v_axis = np.zeros(3), np.zeros(3)
                vtk.vtkMath.Perpendiculars(plane_def['normal'], u_axis, v_axis, 0)
                return {'origin': plane_def['origin'], 'u_axis': u_axis.tolist(), 'v_axis': v_axis.tolist()}
        if isinstance(selection, dict) and 'method' in selection:
            plane_name = selection.get('name')
            if plane_name in self.actor_buffer:
                QMessageBox.critical(self, "Name Conflict", f"An object named '{plane_name}' already exists.")
                return None
            return selection
        self.logger.error(f"Could not resolve plane context for selection: {selection}")
        return None

    def update_plane_context(self, plane_definition: Dict):
        self.current_plane_origin = plane_definition['origin']
        normal = plane_definition['normal']
        u_axis, v_axis = np.zeros(3), np.zeros(3)
        vtk.vtkMath.Perpendiculars(normal, u_axis, v_axis, 0)
        self.current_plane_u_axis = u_axis.tolist()
        self.current_plane_v_axis = v_axis.tolist()

    def get_id_from_actor(self, actor: vtk.vtkActor) -> str | None:
        return next((k for k, v in self.actor_buffer.items() if v == actor), None)

    def is_actor_a_plane(self, actor: vtk.vtkActor) -> bool:
        if not actor: return False
        actor_id = self.get_id_from_actor(actor)
        return actor_id in self.plane_definitions