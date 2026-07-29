import sys
import json
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QFileDialog,
    QScrollArea
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize


# ============================================================
# STORAGE
# ============================================================

DATA_FILE = Path.home() / ".app_suite_launcher.json"


def load_apps():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except:
            return []
    return []


def save_apps(apps):
    DATA_FILE.write_text(json.dumps(apps, indent=4))


# ============================================================
# PARSE .desktop
# ============================================================

def parse_desktop(file_path):
    name = Path(file_path).stem
    icon = None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name="):
                    name = line.split("=", 1)[1]
                elif line.startswith("Icon="):
                    icon = line.split("=", 1)[1]
    except:
        pass

    return name, icon


# ============================================================
# FORMAT NAME
# ============================================================

def format_name(name):
    words = name.split()

    if len(words) <= 1:
        return name

    mid = len(words) // 2
    return "\n".join([
        " ".join(words[:mid]),
        " ".join(words[mid:])
    ])


# ============================================================
# TILE BUTTON
# ============================================================

class AppTile(QPushButton):
    def __init__(self, app, delete_callback):
        super().__init__()

        self.app = app
        self.delete_callback = delete_callback

        # 🔧 tighter tile height (important fix)
        self.setFixedSize(160, 112)

        self.setIconSize(QSize(52, 52))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setText(format_name(app["name"]))

        if app.get("icon"):
            self.setIcon(QIcon.fromTheme(app["icon"]))

        self.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #2A2A2A;
                border-radius: 14px;
                color: #F5F5F5;
                font-size: 12px;
                text-align: center;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #2A2A2A;
                border: 1px solid #FF7A45;
            }

            QPushButton:pressed {
                background-color: #151515;
            }
        """)

        self.clicked.connect(self.launch)

    def launch(self):
        subprocess.Popen(["gtk-launch", Path(self.app["path"]).stem])

    def contextMenuEvent(self, event):
        self.delete_callback(self)


# ============================================================
# MAIN APP
# ============================================================

class AppSuiteLauncher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("App Suite Launcher")
        self.setMinimumSize(750, 520)

        self.apps = load_apps()

        self.layout = QVBoxLayout(self)

        # TOP BAR
        top = QHBoxLayout()

        self.add_btn = QPushButton("Add App")
        self.del_btn = QPushButton("Delete Selected")

        self.add_btn.clicked.connect(self.add_app)
        self.del_btn.clicked.connect(self.delete_selected)

        self.add_btn.setStyleSheet(self.orange_style())
        self.del_btn.setStyleSheet(self.red_style())

        top.addWidget(self.add_btn)
        top.addWidget(self.del_btn)

        self.layout.addLayout(top)

        # SCROLL AREA
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()

        self.grid = QGridLayout(self.container)

        # 🔧 FIXED ROW DENSITY (this is the real solution)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)  # tighter rows
        self.grid.setContentsMargins(14, 10, 14, 10)

        # 🔧 prevents “floating rows”
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self.selected_tile = None

        self.apply_style()
        self.refresh_ui()

    # ========================================================
    # UI REFRESH
    # ========================================================

    def refresh_ui(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row = 0
        col = 0
        max_cols = 4

        for app in self.apps:
            tile = AppTile(app, self.delete_tile)

            tile.clicked.connect(lambda _, t=tile: self.select_tile(t))

            self.grid.addWidget(tile, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    # ========================================================
    # SELECTION
    # ========================================================

    def select_tile(self, tile):
        self.selected_tile = tile

    # ========================================================
    # ADD APP
    # ========================================================

    def add_app(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select .desktop file",
            "/usr/share/applications",
            "Desktop Files (*.desktop)"
        )

        if not file:
            return

        name, icon = parse_desktop(file)

        self.apps.append({
            "name": name,
            "path": file,
            "icon": icon
        })

        save_apps(self.apps)
        self.refresh_ui()

    # ========================================================
    # DELETE APP
    # ========================================================

    def delete_selected(self):
        if not self.selected_tile:
            return

        self.delete_tile(self.selected_tile)
        self.selected_tile = None

    def delete_tile(self, tile):
        self.apps = [
            a for a in self.apps
            if a["path"] != tile.app["path"]
        ]

        save_apps(self.apps)
        self.refresh_ui()

    # ========================================================
    # STYLE
    # ========================================================

    def apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #F5F5F5;
                font-family: Segoe UI;
            }

            QScrollArea {
                border: none;
            }

            QScrollBar:vertical {
                background: #1E1E1E;
                width: 8px;
            }

            QScrollBar::handle:vertical {
                background: #FF7A45;
                border-radius: 4px;
            }
        """)

    def orange_style(self):
        return """
            QPushButton {
                background-color: #FF7A45;
                color: black;
                padding: 8px;
                border-radius: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #FF8C5A;
            }
        """

    def red_style(self):
        return """
            QPushButton {
                background-color: #2A2A2A;
                color: #FF5C5C;
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }

            QPushButton:hover {
                border: 1px solid #FF5C5C;
            }
        """


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Custom Apps")
    app.setDesktopFileName("Custom Apps.desktop")
    w = AppSuiteLauncher()
    w.show()
    sys.exit(app.exec())
