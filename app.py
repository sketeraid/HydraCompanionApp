import sys
import os
import json
import hashlib

from PySide6.QtCore import Qt, QSettings, QEasingCurve, QPropertyAnimation, QRect
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QToolBar,
    QLabel,
    QSizePolicy,
)
from PySide6.QtGui import QAction, QIcon, QPixmap

from ui.dashboard import DashboardTab
from ui.mercy_tracker import MercyTrackerTab
from ui.app_metadata import APP_VERSION, APP_BUILD, APP_THEME_KEY
from ui.settings_page import SettingsPage
from ui.pity import PityPage
from ui.shardinventory import ShardInventory


BUILD_FILE = "build.json"


# ---------------------------------------------------------
#   BUILD SYSTEM HELPERS
# ---------------------------------------------------------

def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_project_hashes(root: str) -> dict:
    hashes = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".py"):
                full_path = os.path.join(dirpath, name)
                rel_path = os.path.relpath(full_path, root)
                try:
                    hashes[rel_path] = hash_file(full_path)
                except Exception:
                    continue
    return hashes


def load_build_info() -> dict:
    if os.path.exists(BUILD_FILE):
        try:
            with open(BUILD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"build": 1, "hashes": {}}


def save_build_info(info: dict):
    with open(BUILD_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)


def update_build_if_needed() -> int:
    root = os.path.dirname(os.path.abspath(__file__))
    current_hashes = collect_project_hashes(root)
    info = load_build_info()

    if info.get("hashes") != current_hashes:
        info["build"] = int(info.get("build", 1)) + 1
        info["hashes"] = current_hashes
        save_build_info(info)

    return int(info.get("build", 1))


# ---------------------------------------------------------
#   GHOST‑FREE ANIMATED STACK
# ---------------------------------------------------------

class AnimatedStack(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim_duration = 250
        self._is_animating = False

    def set_duration(self, ms: int):
        self._anim_duration = ms

    def slide_to_index(self, index: int):
        if index == self.currentIndex() or self._is_animating:
            return

        old_widget = self.currentWidget()
        new_widget = self.widget(index)

        w = self.frameRect().width()
        h = self.frameRect().height()

        direction = 1 if index > self.currentIndex() else -1

        new_widget.setGeometry(QRect(direction * w, 0, w, h))
        new_widget.show()

        old_widget.hide()

        self._is_animating = True

        anim_new = QPropertyAnimation(new_widget, b"geometry", self)
        anim_new.setDuration(self._anim_duration)
        anim_new.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim_new.setStartValue(QRect(direction * w, 0, w, h))
        anim_new.setEndValue(QRect(0, 0, w, h))

        def on_finished():
            self.setCurrentIndex(index)
            new_widget.setGeometry(QRect(0, 0, w, h))
            self._is_animating = False

        anim_new.finished.connect(on_finished)
        anim_new.start()


# ---------------------------------------------------------
#   MAIN WINDOW
# ---------------------------------------------------------

class MainWindow(QWidget):
    def __init__(self, build_number: int):
        super().__init__()

        # Settings + theme
        self.settings = QSettings("SketeRAID", "Hydra Companion")

        if self.settings.value(APP_THEME_KEY) is None:
            self.settings.setValue(APP_THEME_KEY, "dark")

        self.current_theme = self.settings.value(APP_THEME_KEY, "dark")

        # Window setup
        self.setWindowTitle("Hydra Companion")
        self.setMinimumSize(1000, 650)

        self.build_number = build_number
        self.last_page_index = 0

        # Root layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top toolbar
        self.top_bar = QToolBar()
        self.top_bar.setMovable(False)
        root_layout.addWidget(self.top_bar)

        title_label = QLabel("Hydra Companion")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 8px;")
        self.top_bar.addWidget(title_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.top_bar.addWidget(spacer)

        # Navigation actions
        self.action_dashboard = QAction("Dashboard", self)
        self.action_mercy = QAction("Mercy Tracker", self)
        self.action_pity = QAction("Pity", self)
        self.action_settings = QAction("Settings", self)

        self.top_bar.addAction(self.action_dashboard)
        self.top_bar.addAction(self.action_mercy)
        self.top_bar.addAction(self.action_pity)
        self.top_bar.addAction(self.action_settings)

        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.top_bar.addWidget(spacer2)

        # Theme toggle
        self.action_theme_toggle = QAction(self)
        self.update_theme_icon()
        self.top_bar.addAction(self.action_theme_toggle)

        # Top-right logo
        logo_label = QLabel()
        logo_path = os.path.join("logos and assets", "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        logo_label.setContentsMargins(8, 0, 8, 0)
        self.top_bar.addWidget(logo_label)

        root_layout.addSpacing(10)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        root_layout.addLayout(main_layout)

        # Animated stack
        self.stack = AnimatedStack()
        self.stack.set_duration(250)
        main_layout.addWidget(self.stack)

        # Pages
        self.dashboard_tab = DashboardTab()
        self.mercy_tab = MercyTrackerTab()
        self.pity_tab = PityPage()
        self.settings_tab = SettingsPage(self.settings, self.build_number)

        self.stack.addWidget(self.dashboard_tab)   # index 0
        self.stack.addWidget(self.mercy_tab)       # index 1
        self.stack.addWidget(self.pity_tab)        # index 2
        self.stack.addWidget(self.settings_tab)    # index 3

        # Shared shard inventory
        self.inventory = ShardInventory()
        self.dashboard_tab.set_inventory(self.inventory)

        # ⭐ FIX ADDED HERE ⭐
        self.mercy_tab.set_inventory(self.inventory)

        # Pity updates
        self.mercy_tab.pity_updated.connect(self.pity_tab.update_pity)
        self.mercy_tab.pity_updated.connect(self.dashboard_tab.update_pity)

        # Apply theme
        self.apply_theme(self.current_theme)

        # Navigation
        self.action_dashboard.triggered.connect(lambda: self.set_page(0))
        self.action_mercy.triggered.connect(lambda: self.set_page(1))
        self.action_pity.triggered.connect(lambda: self.set_page(2))
        self.action_settings.triggered.connect(lambda: self.set_page(3))

        self.action_theme_toggle.triggered.connect(self.toggle_theme)

        self.set_page(0, animate=False)

    def set_page(self, index: int, animate: bool = True):
        if animate:
            self.stack.slide_to_index(index)
        else:
            self.stack.setCurrentIndex(index)

        self.last_page_index = index
        self.update_active_tab(index)

    def update_active_tab(self, index: int):
        actions = [
            self.action_dashboard,
            self.action_mercy,
            self.action_pity,
            self.action_settings,
        ]

        toolbar_buttons = []
        for i in range(self.top_bar.layout().count()):
            widget = self.top_bar.layout().itemAt(i).widget()
            if widget and widget.metaObject().className() == "QToolButton":
                toolbar_buttons.append(widget)

        for i, button in enumerate(toolbar_buttons):
            is_active = (i == index)
            button.setProperty("active", is_active)
            button.style().unpolish(button)
            button.style().polish(button)

    # ---------------- THEME METHODS ----------------

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.settings.setValue(APP_THEME_KEY, self.current_theme)

        self.apply_theme(self.current_theme)
        self.update_theme_icon()

        self.settings_tab.refresh_theme_label()

    def update_theme_icon(self):
        if self.current_theme == "dark":
            self.action_theme_toggle.setText("Light Mode")
        else:
            self.action_theme_toggle.setText("Dark Mode")

    def apply_theme(self, theme: str):
        if theme == "dark":
            self.setStyleSheet(self.dark_stylesheet())
        else:
            self.setStyleSheet(self.light_stylesheet())

        self.pity_tab.set_theme(theme)
        self.dashboard_tab.set_theme(theme)

    def dark_stylesheet(self) -> str:
        return """
        QWidget {
            background-color: #000000;
            color: #f0f0f0;
        }
        QToolBar {
            background-color: #0a0a0a;
            border-bottom: 1px solid #222;
        }
        QToolButton {
            padding: 6px 14px;
            font-weight: bold;
            border-radius: 10px;
            background-color: #111;
            border: 2px solid #222;
            color: #f0f0f0;
        }
        QToolButton:hover {
            border: 2px solid #66ff66;
            background-color: #151515;
            box-shadow: 0 0 8px #66ff66;
        }
        QToolButton[active="true"] {
            border: 2px solid #99ff99;
            background-color: #0d0d0d;
            box-shadow: 0 0 12px #99ff99;
        }
        QToolButton:pressed {
            background-color: #222;
        }
        """

    def light_stylesheet(self) -> str:
        return """
        QWidget {
            background-color: #f5f5f5;
            color: #202020;
        }
        QToolBar {
            background-color: #e0e0e0;
            border-bottom: 1px solid #c0c0c0;
        }
        QToolButton {
            padding: 6px 14px;
            font-weight: bold;
            border: 2px solid transparent;
            border-radius: 10px;
            background-color: transparent;
        }
        QToolButton:hover {
            border: 2px solid #225522;
            background-color: #f0f0f0;
        }
        QToolButton[active="true"] {
            border: 2px solid #337733;
            background-color: #dff5df;
        }
        QToolButton:pressed {
            background-color: #cfcfcf;
        }
        """

# ---------------------------------------------------------
#   ENTRY POINT
# ---------------------------------------------------------

def main():
    build_number = update_build_if_needed()
    app = QApplication(sys.argv)

    icon_path = os.path.join("logos and assets", "logo.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow(build_number)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()