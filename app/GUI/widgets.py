# File: app/GUI/widgets.py
"""
Defines custom PyQt widgets for the application, such as the Status Window
logger and the interactive Object Browser.
"""
import logging
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QMenu, QTextEdit, QTreeWidgetItem, QTreeWidget


class QtLogHandler(logging.Handler, QObject):
    """
    A custom logging handler that emits a signal for each log record.
    This decouples the logger from the specific UI widget and allows the main
    window to route messages as needed (e.g., to status or error windows).
    """
    log_record_emitted = pyqtSignal(logging.LogRecord)

    def __init__(self, parent=None):
        super().__init__()
        QObject.__init__(self) # QObject must be initialized for signals
        self.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))

    def emit(self, record):
        """Emits the log record via a PyQt signal."""
        self.log_record_emitted.emit(record)


class ObjectBrowser(QTreeWidget):
    """A tree widget to display and manage scene objects hierarchically."""
    object_delete_requested = pyqtSignal(str, str)
    object_rename_requested = pyqtSignal(str, str)
    object_visibility_toggled = pyqtSignal(str)
    object_set_active_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Object", "Type"])
        self.setColumnWidth(0, 200)
        self.active_plane_id: str | None = None
        self.active_cs_title: str = "Global"
        self._create_top_level_nodes()

    def _create_top_level_nodes(self):
        """Creates the main category nodes in the tree."""
        self.primitives_node = QTreeWidgetItem(self, ["Primitives"])
        self.imports_node = QTreeWidgetItem(self, ["Imports"])
        self.planes_node = QTreeWidgetItem(self, ["Planes"])
        self.coordinate_systems_node = QTreeWidgetItem(self, ["Coordinate Systems"])
        self.expandAll()
    
    def set_active_plane_id(self, obj_id: str | None):
        self.active_plane_id = obj_id

    def set_active_cs_title(self, title: str):
        self.active_cs_title = title

    def clear(self):
        super().clear()
        self._create_top_level_nodes()

    def add_object(self, obj_id: str, obj_type: str, category: str, parent_id: str = None):
        parent_node = None
        if parent_id:
            items = self.findItems(parent_id, Qt.MatchExactly | Qt.MatchRecursive, column=0)
            if items: parent_node = items[0]
        else:
            if category.lower() == "imports": parent_node = self.imports_node
            elif category.lower() == "planes": parent_node = self.planes_node
            elif category.lower() == "coordinate systems": parent_node = self.coordinate_systems_node
            else: parent_node = self.primitives_node
        if parent_node is None:
            parent_node = self.imports_node if category.lower() == "imports" else self.primitives_node
        
        item = QTreeWidgetItem(parent_node, [obj_id, obj_type.capitalize()])
        item.setData(0, Qt.UserRole, obj_id)
        item.setData(1, Qt.UserRole, category)
        parent_node.setExpanded(True)

    def remove_object(self, obj_id: str):
        items = self.findItems(obj_id, Qt.MatchExactly | Qt.MatchRecursive, column=0)
        if items:
            (items[0].parent() or self).removeChild(items[0])

    def update_object_name(self, old_id: str, new_id: str):
        items = self.findItems(old_id, Qt.MatchExactly | Qt.MatchRecursive, column=0)
        if items:
            items[0].setText(0, new_id)
            items[0].setData(0, Qt.UserRole, new_id)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not (item and item.parent()): return

        obj_id = item.data(0, Qt.UserRole)
        category = item.data(1, Qt.UserRole)
        if not obj_id: return

        menu = QMenu(self)
        is_lcs = (category == "Coordinate Systems")
        is_plane = (category == "Planes")

        set_active_action = menu.addAction("Set Active") if is_lcs else None
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        toggle_vis_action = menu.addAction("Show / Hide")

        toggle_vis_action.setVisible(not is_lcs)
        if set_active_action: set_active_action.setVisible(is_lcs)

        if is_lcs:
            if obj_id == "Global":
                rename_action.setEnabled(False); delete_action.setEnabled(False)
                rename_action.setToolTip("Cannot rename the Global coordinate system.")
                delete_action.setToolTip("Cannot delete the Global coordinate system.")
            if obj_id == self.active_cs_title:
                delete_action.setEnabled(False)
                delete_action.setToolTip("Cannot delete the active coordinate system.")
                set_active_action.setEnabled(False)
        if is_plane and obj_id == self.active_plane_id:
            delete_action.setEnabled(False)
            delete_action.setToolTip("Cannot delete the active working plane.")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == delete_action: self.object_delete_requested.emit(obj_id, category)
        elif action == rename_action: self.object_rename_requested.emit(obj_id, category)
        elif action == toggle_vis_action: self.object_visibility_toggled.emit(obj_id)
        elif action == set_active_action: self.object_set_active_requested.emit(obj_id)