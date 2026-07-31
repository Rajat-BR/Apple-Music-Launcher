import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

BANNER_PATH = Path(__file__).parent / "banner.png"

WINDOW_WIDTH = 420
WINDOW_HEIGHT = 560
BANNER_DISPLAY_WIDTH = 360
BUTTON_HEIGHT = 44

DARK_STYLESHEET = """
QWidget {
    background-color: #000000;
    color: #E0E0E0;
    font-family: "Helvetica Neue", sans-serif;
}

QPushButton {
    background-color: #1E1E1E;
    border: 1px solid #700000;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    color: #E0E0E0;
}

QPushButton:hover {
    background-color: #B00000;
    border: 1px solid #B00000;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #700000;
}

QLabel#statusLabel {
    color: #999999;
    font-size: 12px;
}
"""


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Apple Music Launcher")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- Banner ---
        self.banner_label = QLabel()
        self.banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._load_banner()
        layout.addWidget(self.banner_label)

        layout.addStretch(1)

        # --- Buttons ---
        self.launch_button = QPushButton("Launch Apple Music")
        self.refresh_button = QPushButton("Refresh Login")
        self.exit_button = QPushButton("Exit")

        for button in (self.launch_button, self.refresh_button, self.exit_button):
            button.setFixedHeight(BUTTON_HEIGHT)
            layout.addWidget(button)

        layout.addStretch(1)

        # --- Status label (for later phases) ---
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)

        # Phase 1: exit is the only wired action, since it needs no backend call.
        self.exit_button.clicked.connect(self.close)

        self._center_on_screen()

    def _center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def _load_banner(self):
        if BANNER_PATH.exists():
            pixmap = QPixmap(str(BANNER_PATH))
            pixmap = pixmap.scaledToWidth(
                BANNER_DISPLAY_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
            self.banner_label.setPixmap(pixmap)
        else:
            self.banner_label.setText("Apple Music")
            self.banner_label.setStyleSheet(
                "font-size: 22px; font-weight: bold; color: #B00000;"
            )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()