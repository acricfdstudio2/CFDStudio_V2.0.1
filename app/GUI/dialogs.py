# File: app/GUI/dialogs.py
"""
A collection of standardized input dialogs for the application.
"""

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
# MODIFICATION: QFileDialog has been correctly added to the import statement.
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QRadioButton,
                             QPushButton, QSpinBox, QTabWidget, QVBoxLayout,
                             QWidget)


class PointInputWidget(QGroupBox):
    """
    A reusable and robust widget for defining a 3D point via manual input
    or interactive on-screen picking.
    """
    pickFromScreenRequested = pyqtSignal()

    def __init__(self, title="Point", parent=None):
        super().__init__(title, parent)
        self.main_layout = QHBoxLayout(self)

        # Coordinate Inputs
        self.x_input = QLineEdit("0.0"); self.x_input.setValidator(QDoubleValidator())
        self.y_input = QLineEdit("0.0"); self.y_input.setValidator(QDoubleValidator())
        self.z_input = QLineEdit("0.0"); self.z_input.setValidator(QDoubleValidator())

        form_layout = QFormLayout()
        form_layout.addRow("X:", self.x_input)
        form_layout.addRow("Y:", self.y_input)
        form_layout.addRow("Z:", self.z_input)
        self.main_layout.addLayout(form_layout)

        # The "Pick" button - clear and explicit
        self.pick_screen_button = QPushButton("Pick")
        self.pick_screen_button.setToolTip("Select a point from the 3D scene")
        # In a real app, you would add an icon:
        # from PyQt5.QtGui import QIcon
        # self.pick_screen_button.setIcon(QIcon("path/to/crosshair_icon.png"))
        self.pick_screen_button.clicked.connect(self.pickFromScreenRequested.emit)
        self.main_layout.addWidget(self.pick_screen_button)

    def get_point(self) -> Optional[List[float]]:
        """Returns the coordinates as a list of floats, or None if invalid."""
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            return [x, y, z]
        except (ValueError, TypeError):
            return None

    def set_point(self, point: List[float]):
        """Updates the line edits with the given coordinates."""
        if len(point) == 3:
            self.x_input.setText(f"{point[0]:.4f}")
            self.y_input.setText(f"{point[1]:.4f}")
            self.z_input.setText(f"{point[2]:.4f}")

class PlaneSelectionWidget(QGroupBox):
    """A reusable widget that provides all options for selecting a plane."""
    def __init__(self, existing_planes: List[str], parent=None):
        super().__init__("Select Base Plane", parent)
        layout = QVBoxLayout(self)
        self.rb_active = QRadioButton("Use the Current Active Working Plane")
        self.rb_active.setChecked(True)
        self.rb_global = QRadioButton("Use the Global XY Plane (at origin)")
        self.rb_existing = QRadioButton("Select an Existing Plane:")
        self.rb_define = QRadioButton("Define a New Plane for this operation")
        self.combo_existing_planes = QComboBox()
        self.combo_existing_planes.addItems(existing_planes)
        self.combo_existing_planes.setEnabled(False)
        self.rb_existing.toggled.connect(self.combo_existing_planes.setEnabled)
        if not existing_planes:
            self.rb_existing.setEnabled(False)
            self.rb_existing.setToolTip("No other planes have been created yet.")
        for widget in [self.rb_active, self.rb_global, self.rb_existing,
                       self.combo_existing_planes, self.rb_define]:
            layout.addWidget(widget)

    def get_selection_result(self, parent_dialog) -> Dict[str, Any] | str | None:
        if self.rb_active.isChecked(): return "active"
        elif self.rb_global.isChecked(): return {'origin': [0.0,0.0,0.0], 'u_axis': [1.0,0.0,0.0], 'v_axis': [0.0,1.0,0.0]}
        elif self.rb_existing.isChecked(): return self.combo_existing_planes.currentText()
        elif self.rb_define.isChecked():
            dialog = PlaneCreationDialog(parent_dialog)
            if dialog.exec_() and dialog.result_data:
                return dialog.result_data
        return None

class PlaneCreationDialog(QDialog):
    """A dialog for creating a new plane from user input."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Define New Plane From Input")
        self.setMinimumWidth(350)
        self.result_data = None
        layout = QVBoxLayout(self)
        name_layout = QFormLayout()
        self.plane_name_input = QLineEdit(f"Plane_{id(self)}")
        name_layout.addRow("Plane Name:", self.plane_name_input)
        layout.addLayout(name_layout)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_point_vector_ui(), "Point + Normal Vector")
        self.tabs.addTab(self._create_three_points_ui(), "Three Points")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.tabs)
        layout.addWidget(self.button_box)

    def _create_point_vector_ui(self) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        self.pv_origin_input = QLineEdit("0, 0, 0")
        self.pv_normal_input = QLineEdit("0, 0, 1")
        layout.addRow("Origin (x, y, z):", self.pv_origin_input)
        layout.addRow("Normal (i, j, k):", self.pv_normal_input)
        return widget

    def _create_three_points_ui(self) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        self.tp_p1_input = QLineEdit("0, 0, 0")
        self.tp_p2_input = QLineEdit("1, 0, 0")
        self.tp_p3_input = QLineEdit("0, 1, 0")
        layout.addRow("Point 1 (x, y, z):", self.tp_p1_input)
        layout.addRow("Point 2 (x, y, z):", self.tp_p2_input)
        layout.addRow("Point 3 (x, y, z):", self.tp_p3_input)
        return widget

    def _parse_vector(self, text: str) -> Optional[List[float]]:
        try:
            parts = [float(p.strip()) for p in text.split(',')]; return parts if len(parts) == 3 else None
        except (ValueError, TypeError): return None

    def on_accept(self):
        plane_name = self.plane_name_input.text().strip()
        if not plane_name: QMessageBox.critical(self, "Input Error", "Plane name cannot be empty."); return
        if self.tabs.currentIndex() == 0:
            origin = self._parse_vector(self.pv_origin_input.text())
            normal = self._parse_vector(self.pv_normal_input.text())
            if origin is None or normal is None: QMessageBox.critical(self, "Input Error", "Invalid vector format."); return
            self.result_data = {'method': 'point_vector', 'origin': origin, 'normal': normal}
        else:
            p1 = self._parse_vector(self.tp_p1_input.text()); p2 = self._parse_vector(self.tp_p2_input.text()); p3 = self._parse_vector(self.tp_p3_input.text())
            if p1 is None or p2 is None or p3 is None: QMessageBox.critical(self, "Input Error", "Invalid vector format."); return
            self.result_data = {'method': 'three_points', 'p1': p1, 'p2': p2, 'p3': p3}
        self.result_data['name'] = plane_name
        self.accept()

class SelectBasePlaneDialog(QDialog):
    """A simple dialog that just wraps the PlaneSelectionWidget."""
    def __init__(self, existing_planes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Base Plane")
        self.plane_context = None

        main_layout = QVBoxLayout(self)
        self.plane_selector = PlaneSelectionWidget(existing_planes, self)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.plane_selector)
        main_layout.addWidget(self.button_box)

    def _on_accept(self):
        self.plane_context = self.plane_selector.get_selection_result(self)
        if self.plane_context:
            self.accept()


class BaseCreationDialog(QDialog):
    """An abstract base class for primitive creation dialogs."""
    def __init__(self, title: str, existing_planes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.params: Optional[tuple] = None
        self.plane_context: Optional[dict | str] = None

        main_layout = QVBoxLayout(self)
        self.input_widget = self._create_input_widget()
        self.plane_selector = PlaneSelectionWidget(existing_planes)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.input_widget)
        main_layout.addWidget(self.plane_selector)
        main_layout.addWidget(self.button_box)

    def _create_input_widget(self) -> QWidget: raise NotImplementedError
    def _on_accept(self) -> None: raise NotImplementedError


class PointDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.u_input = QLineEdit("0")
        self.v_input = QLineEdit("0")
        layout.addRow("Plane Coordinate (u):", self.u_input)
        layout.addRow("Plane Coordinate (v):", self.v_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            u = float(self.u_input.text())
            v = float(self.v_input.text())
            plane = self.plane_selector.get_selection_result(self)
        except (ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid coordinate format."); return
        if plane:
            self.params = (u, v)
            self.plane_context = plane
            self.accept()


class LineDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.p1_input = QLineEdit("0,0")
        self.p2_input = QLineEdit("10,10")
        layout.addRow("Start Point (u,v):", self.p1_input)
        layout.addRow("End Point (u,v):", self.p2_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            u1, v1 = map(float, self.p1_input.text().split(','))
            u2, v2 = map(float, self.p2_input.text().split(','))
        except (ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid coordinate format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (u1, v1, u2, v2)
            self.plane_context = plane
            self.accept()


class TriangleDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.p1_input = QLineEdit("0,0")
        self.p2_input = QLineEdit("10,0")
        self.p3_input = QLineEdit("5,10")
        layout.addRow("Point 1 (u,v):", self.p1_input)
        layout.addRow("Point 2 (u,v):", self.p2_input)
        layout.addRow("Point 3 (u,v):", self.p3_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            u1, v1 = map(float, self.p1_input.text().split(','))
            u2, v2 = map(float, self.p2_input.text().split(','))
            u3, v3 = map(float, self.p3_input.text().split(','))
        except(ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid coordinate format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (u1, v1, u2, v2, u3, v3)
            self.plane_context = plane
            self.accept()


class CircleDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.center_input = QLineEdit("0,0")
        self.radius_input = QLineEdit("5")
        layout.addRow("Center (cu,cv):", self.center_input)
        layout.addRow("Radius (r):", self.radius_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            cu, cv = map(float, self.center_input.text().split(','))
            r = float(self.radius_input.text())
        except (ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid input format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (cu, cv, r)
            self.plane_context = plane
            self.accept()


class CuboidDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.side_input = QLineEdit("10.0")
        layout.addRow("Side Length:", self.side_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            side = float(self.side_input.text())
        except (ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid number format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (side,)
            self.plane_context = plane
            self.accept()


class CubeDialog(CuboidDialog): 
    pass
class SphereDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.radius_input = QLineEdit("5.0")
        layout.addRow("Radius:", self.radius_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            radius = float(self.radius_input.text())
        except(ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid number format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (radius,)
            self.plane_context = plane
            self.accept()

class CylinderDialog(BaseCreationDialog):
    def _create_input_widget(self) -> QWidget:
        widget, layout = QWidget(), QFormLayout()
        self.radius_input = QLineEdit("3.0")
        self.height_input = QLineEdit("10.0")
        layout.addRow("Radius:", self.radius_input)
        layout.addRow("Height:", self.height_input)
        widget.setLayout(layout)
        return widget

    def _on_accept(self):
        try:
            r = float(self.radius_input.text())
            h = float(self.height_input.text())
        except(ValueError, TypeError):
            QMessageBox.critical(self, "Input Error", "Invalid number format."); return
        plane = self.plane_selector.get_selection_result(self)
        if plane:
            self.params = (r, h)
            self.plane_context = plane
            self.accept()

class ConeDialog(CylinderDialog): 
    pass

class PointInputWidget(QWidget):
    """A reusable widget for X,Y,Z input with a selection button."""
    selectionRequested = pyqtSignal()
    validityChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line_edits = []
        for label in ["X:", "Y:", "Z:"]:
            layout.addWidget(QLabel(label))
            line_edit = QLineEdit("0.0")
            line_edit.setValidator(QDoubleValidator())
            line_edit.textChanged.connect(self._check_validity)
            self.line_edits.append(line_edit)
            layout.addWidget(line_edit)

        self.select_button = QPushButton("...")
        self.select_button.setFixedSize(24, 24)
        self.select_button.setToolTip("Select point from 3D view")
        self.select_button.clicked.connect(self.selectionRequested.emit)
        layout.addWidget(self.select_button)

    def _check_validity(self):
        is_valid = all(le.hasAcceptableInput() and le.text() for le in self.line_edits)
        self.validityChanged.emit(is_valid)

    def get_point(self) -> Optional[tuple[float, ...]]:
        try:
            return tuple(float(le.text()) for le in self.line_edits)
        except ValueError:
            return None

    def set_point(self, point_tuple: tuple):
        for i, coord in enumerate(point_tuple):
            self.line_edits[i].setText(str(coord))
        self._check_validity()

class BaseDefinitionWidget(QWidget):
    """Abstract base class for CS definition method widgets."""
    validityChanged = pyqtSignal(bool)
    selectionRequested = pyqtSignal(QObject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.point_widgets: List[PointInputWidget] = []

    def check_form_validity(self):
        is_valid = all(pw.get_point() is not None for pw in self.point_widgets)
        self.validityChanged.emit(is_valid)

    def get_data(self) -> dict:
        raise NotImplementedError

class ThreePointDefinitionWidget(BaseDefinitionWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self.origin_input = PointInputWidget()
        self.x_axis_input = PointInputWidget()
        self.xy_plane_input = PointInputWidget()
        self.point_widgets = [self.origin_input, self.x_axis_input, self.xy_plane_input]

        for pw in self.point_widgets:
            pw.validityChanged.connect(self.check_form_validity)
            pw.selectionRequested.connect(lambda pw=pw: self.selectionRequested.emit(pw))
        
        layout.addRow("Origin:", self.origin_input)
        layout.addRow("Point on X-Axis:", self.x_axis_input)
        layout.addRow("Point in XY-Plane:", self.xy_plane_input)
    
    def get_data(self) -> dict:
        return {
            "origin": self.origin_input.get_point(),
            "point_on_x": self.x_axis_input.get_point(),
            "point_in_xy": self.xy_plane_input.get_point()
        }

class OriginVectorsDefinitionWidget(BaseDefinitionWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self.origin_input = PointInputWidget()
        self.x_dir_input = PointInputWidget()
        self.y_dir_input = PointInputWidget()
        self.point_widgets = [self.origin_input, self.x_dir_input, self.y_dir_input]
        
        for pw in self.point_widgets:
            pw.validityChanged.connect(self.check_form_validity)
            pw.selectionRequested.connect(lambda pw=pw: self.selectionRequested.emit(pw))

        layout.addRow("Origin:", self.origin_input)
        layout.addRow("X-Direction Vector:", self.x_dir_input)
        layout.addRow("Y-Direction Vector:", self.y_dir_input)
        
    def get_data(self) -> dict:
        return {
            "origin": self.origin_input.get_point(),
            "x_dir": self.x_dir_input.get_point(),
            "y_dir": self.y_dir_input.get_point()
        }

class CoordinateSystemCreatorDialog(QDialog):
    coordinateSystemCreated = pyqtSignal(str, dict)
    selectionRequested = pyqtSignal(QObject)

    def __init__(self, default_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Local Coordinate System")
        self.setMinimumWidth(450)
        
        main_layout = QVBoxLayout(self)

        settings_group = QGroupBox("General Settings")
        settings_layout = QFormLayout()
        
        self.cs_title_input = QLineEdit(default_title)
        self.cs_title_input.textChanged.connect(self._check_overall_validity)
        
        self.set_active_checkbox = QCheckBox("Set as active after creation")
        self.set_active_checkbox.setChecked(True)
        
        settings_layout.addRow("Title:", self.cs_title_input)
        settings_layout.addRow(self.set_active_checkbox)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        self.tabs = QTabWidget()
        self.method_widgets = {
            "3_points": ThreePointDefinitionWidget(),
            "origin_vectors": OriginVectorsDefinitionWidget()
        }
        self.tabs.addTab(self.method_widgets["3_points"], "By 3 Points")
        self.tabs.addTab(self.method_widgets["origin_vectors"], "By Origin & Vectors")
        main_layout.addWidget(self.tabs)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setText("Create")
        main_layout.addWidget(self.button_box)
        
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        
        for widget in self.method_widgets.values():
            widget.selectionRequested.connect(self.selectionRequested.emit)
            widget.validityChanged.connect(self._check_overall_validity)

        self.tabs.currentChanged.connect(self._check_overall_validity)
        self._check_overall_validity()

    def _check_overall_validity(self):
        """Central validation for enabling the 'Create' button."""
        is_title_valid = bool(self.cs_title_input.text().strip())
        current_widget = self.tabs.currentWidget()
        are_points_valid = all(pw.get_point() is not None for pw in current_widget.point_widgets)
        self.ok_button.setEnabled(is_title_valid and are_points_valid)

    def on_accept(self):
        current_idx = self.tabs.currentIndex()
        method_name = list(self.method_widgets.keys())[current_idx]
        widget = self.method_widgets[method_name]
        
        data = widget.get_data()
        data["title"] = self.cs_title_input.text().strip()
        data["set_active"] = self.set_active_checkbox.isChecked()
        
        self.coordinateSystemCreated.emit(method_name, data)
        self.accept()

class PointSelectionWidget(QGroupBox):
    """A widget for defining a 3D point via input or interactive picking."""
    pickFromScreenRequested = pyqtSignal()

    def __init__(self, title="Origin", parent=None):
        super().__init__(title, parent)
        self.main_layout = QHBoxLayout(self)
        
        self.x_input = QLineEdit("0.0"); self.x_input.setValidator(QDoubleValidator())
        self.y_input = QLineEdit("0.0"); self.y_input.setValidator(QDoubleValidator())
        self.z_input = QLineEdit("0.0"); self.z_input.setValidator(QDoubleValidator())

        form_layout = QFormLayout()
        form_layout.addRow("X:", self.x_input)
        form_layout.addRow("Y:", self.y_input)
        form_layout.addRow("Z:", self.z_input)
        self.main_layout.addLayout(form_layout)

        pick_button_layout = QVBoxLayout()
        self.pick_screen_button = QPushButton("Pick from Screen")
        self.pick_screen_button.clicked.connect(self.pickFromScreenRequested.emit)
        pick_button_layout.addWidget(self.pick_screen_button)
        self.main_layout.addLayout(pick_button_layout)

    def get_point(self) -> Optional[List[float]]:
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            return [x, y, z]
        except (ValueError, TypeError):
            return None

    def set_point(self, point: List[float]):
        if len(point) == 3:
            self.x_input.setText(f"{point[0]:.4f}")
            self.y_input.setText(f"{point[1]:.4f}")
            self.z_input.setText(f"{point[2]:.4f}")

class DxfImportDialog(QDialog):
    """A comprehensive dialog for setting up a DXF import operation."""
    def __init__(self, existing_planes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import DXF File")
        self.setMinimumWidth(500)
        
        self.result_data = None
        main_layout = QVBoxLayout(self)

        file_group = QGroupBox("File")
        file_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select a .dxf file...")
        self.path_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_for_file)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_button)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        self.origin_widget = PointSelectionWidget("Import Origin", self)
        main_layout.addWidget(self.origin_widget)

        self.plane_widget = PlaneSelectionWidget(existing_planes, self)
        main_layout.addWidget(self.plane_widget)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Import")
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _browse_for_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Open DXF File", "", "DXF Files (*.dxf);;All Files (*)")
        if fp:
            self.path_edit.setText(fp)

    def on_accept(self):
        filepath = self.path_edit.text()
        if not filepath:
            QMessageBox.critical(self, "Input Error", "You must select a DXF file to import.")
            return
        origin = self.origin_widget.get_point()
        if origin is None:
            QMessageBox.critical(self, "Input Error", "The origin coordinates are invalid.")
            return
        plane_context = self.plane_widget.get_selection_result(self)
        if plane_context is None:
            return
        self.result_data = {
            "filepath": filepath,
            "origin": origin,
            "plane_context": plane_context
        }
        self.accept()


class CuboidByDimensionsWidget(QWidget):
    """UI for creating a cuboid from dimensions, center, and orientation."""
    def __init__(self, existing_planes, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.length_input = QLineEdit("10.0"); self.length_input.setValidator(QDoubleValidator(0.001, 1e9, 4))
        self.width_input = QLineEdit("5.0"); self.width_input.setValidator(QDoubleValidator(0.001, 1e9, 4))
        self.height_input = QLineEdit("2.0"); self.height_input.setValidator(QDoubleValidator(0.001, 1e9, 4))
        form_layout.addRow("Length (X):", self.length_input)
        form_layout.addRow("Width (Y):", self.width_input)
        form_layout.addRow("Height (Z):", self.height_input)
        layout.addLayout(form_layout)
        self.center_widget = PointInputWidget("Center Point", self)
        layout.addWidget(self.center_widget)
        self.plane_widget = PlaneSelectionWidget(existing_planes, self)
        self.plane_widget.setTitle("Orientation")
        layout.addWidget(self.plane_widget)

class CuboidByCornersWidget(QWidget):
    """UI for creating a cuboid from two opposite corner points."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.corner1_widget = PointInputWidget("First Corner", self)
        self.corner2_widget = PointInputWidget("Second Corner", self)
        layout.addWidget(self.corner1_widget)
        layout.addWidget(self.corner2_widget)

class CuboidCreationDialog(QDialog):
    """A dialog with tabs for creating a cuboid via different methods."""
    def __init__(self, existing_planes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Solid Cuboid")
        self.setMinimumWidth(450)
        self.result_data = None
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.dim_tab = CuboidByDimensionsWidget(existing_planes)
        self.cor_tab = CuboidByCornersWidget()
        self.tabs.addTab(self.dim_tab, "By Dimensions")
        self.tabs.addTab(self.cor_tab, "By Corners")
        main_layout.addWidget(self.tabs)
        self.dim_tab.center_widget.pickFromScreenRequested.connect(lambda: parent.start_point_picking_mode(self.dim_tab.center_widget))
        self.cor_tab.corner1_widget.pickFromScreenRequested.connect(lambda: parent.start_point_picking_mode(self.cor_tab.corner1_widget))
        self.cor_tab.corner2_widget.pickFromScreenRequested.connect(lambda: parent.start_point_picking_mode(self.cor_tab.corner2_widget))
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def on_accept(self):
        if self.tabs.currentIndex() == 0:
            try:
                l = float(self.dim_tab.length_input.text()); w = float(self.dim_tab.width_input.text()); h = float(self.dim_tab.height_input.text())
                center = self.dim_tab.center_widget.get_point()
                plane_sel = self.dim_tab.plane_widget.get_selection_result(self)
                if not all([l > 0, w > 0, h > 0]): raise ValueError("Dimensions must be positive.")
                if center is None: raise ValueError("Invalid center point coordinates.")
                if plane_sel is None: return
                self.result_data = {"method": "dimensions", "dimensions": (l, w, h), "center": center, "plane_selection": plane_sel}
            except (ValueError, TypeError) as e:
                QMessageBox.critical(self, "Input Error", f"Invalid input for dimensions or center point: {e}"); return
        else:
            p1 = self.cor_tab.corner1_widget.get_point(); p2 = self.cor_tab.corner2_widget.get_point()
            if p1 is None or p2 is None: QMessageBox.critical(self, "Input Error", "Invalid coordinates for one or both corner points."); return
            self.result_data = {"method": "corners", "p1": p1, "p2": p2}
        self.accept()
