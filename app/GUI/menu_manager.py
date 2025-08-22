"""Module for building the main menu bar from a JSON configuration file."""

import json
from PyQt5.QtWidgets import QAction


class MenuManager:
    """Builds the main menu bar from a JSON configuration file."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.menu_bar = self.main_window.menuBar()

    def build_menus(self, filepath="menu.json"):
        """Loads a JSON file and builds the menu structure from it."""
        try:
            with open(filepath, 'r') as f:
                menu_data = json.load(f)
            for menu_title, menu_items in menu_data.items():
                menu = self.menu_bar.addMenu(f"&{menu_title}")
                self._populate_menu(menu, menu_items)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading menu file '{filepath}': {e}")
            # Optionally, create a default menu here as a fallback

    def _populate_menu(self, parent_menu, items_dict: dict):
        """Recursively populates a menu or submenu with actions and submenus."""
        for text, value in items_dict.items():
            if value == "separator":
                parent_menu.addSeparator()
            elif isinstance(value, dict):
                submenu = parent_menu.addMenu(text)
                self._populate_menu(submenu, value)
            elif isinstance(value, str):
                action = QAction(text, self.main_window)
                # Connect the action's trigger to the main window's central handler
                action.triggered.connect(lambda checked=False, action_id=value:
                                         self.main_window.handle_action(action_id))

                # Set shortcuts for common actions
                if value == "undo": action.setShortcut("Ctrl+Z")
                if value == "redo": action.setShortcut("Ctrl+Y")
                if value == "delete_object": action.setShortcut("Del")
                if value == "exit_app": action.setShortcut("Ctrl+Q")

                parent_menu.addAction(action)