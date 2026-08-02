import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QSizePolicy,
    QMessageBox,
    QDialog,
    QLineEdit,
    QDialogButtonBox,
    QProgressBar,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal

from launcher_backend import launch, refresh_login, load_config, LauncherError

BANNER_PATH = Path(__file__).parent / "banner.png"

WINDOW_WIDTH = 420
WINDOW_HEIGHT = 560
BANNER_DISPLAY_WIDTH = 360
BUTTON_HEIGHT = 44

DARK_STYLESHEET = """
QWidget {
    background-color: #121212;
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

QLineEdit {
    background-color: #1E1E1E;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 8px;
    color: #E0E0E0;
    selection-background-color: #B00000;
}

QLineEdit:focus {
    border: 1px solid #B00000;
}

QProgressBar {
    background-color: #1E1E1E;
    border: 1px solid #444444;
    border-radius: 3px;
    height: 6px;
}

QProgressBar::chunk {
    background-color: #B00000;
    border-radius: 3px;
}
"""


class BackendWorker(QThread):
    """
    Runs a single backend callable (e.g. launch, refresh_login) on a
    background thread so the GUI stays responsive. Does not alter the
    callable in any way. Backend functions now return normally on
    success and raise LauncherError (or another exception) on
    failure, so we just need to catch and report.

    Every backend entry point (launch, refresh_login) accepts an
    optional status_callback keyword argument - this worker always
    supplies its own status_signal.emit as that callback, so backend
    progress messages (the same ones the CLI prints) reach the GUI
    without any string duplication. Qt marshals the emit() call from
    this thread to the main-thread slot automatically.
    """

    finished_signal = pyqtSignal(bool, str)
    status_signal = pyqtSignal(str)

    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self._target(
                *self._args,
                status_callback=self.status_signal.emit,
                **self._kwargs,
            )
        except LauncherError as exc:
            # Expected backend failure (bad config, docker not found, timeout, etc.)
            self.finished_signal.emit(False, str(exc))
            return
        except Exception as exc:
            # Unexpected bug - still reported the same way, but kept
            # separate so it's obvious in the code which case is which.
            self.finished_signal.emit(False, str(exc))
            return

        self.finished_signal.emit(True, "")


class LoginDialog(QDialog):
    """
    Collects an Apple ID and password, replacing the terminal
    input()/getpass() prompts that login_wrapper() used to do itself.
    The credentials are only handed to the backend on accept - this
    dialog has no knowledge of Docker or the wrapper container.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wrapper Login")
        self.setFixedWidth(320)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@example.com")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")

        form_layout = QFormLayout()
        form_layout.addRow("Apple ID:", self.email_input)
        form_layout.addRow("Password:", self.password_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.email = ""
        self.password = ""

    def _on_accept(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(
                self, "Missing Information", "Apple ID and password are both required."
            )
            return

        self.email = email
        self.password = password
        self.accept()


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

        # --- Busy indicator ---
        # QProgressBar's built-in indeterminate ("marquee") animation
        # doesn't reliably animate once a QSS stylesheet is applied to
        # it, so we drive a bouncing fill manually with a QTimer -
        # this guarantees visible motion regardless of platform/style.
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(20)
        self._progress_timer.timeout.connect(self._animate_progress)
        self._progress_value = 0
        self._progress_direction = 1

        # --- Status label ---
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)

        # Phase 2: launch and refresh now run on background threads.
        self.launch_button.clicked.connect(self._on_launch_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.exit_button.clicked.connect(self.close)

        self._center_on_screen()

        # Keep references to running workers so they aren't garbage collected mid-run.
        self._active_worker = None
        self._close_on_success = False

    def _set_buttons_enabled(self, enabled):
        self.launch_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)

    def _run_backend(self, target, status_message, *args, close_on_success=False, **kwargs):
        self._set_buttons_enabled(False)
        self.status_label.setText(status_message)
        self._progress_value = 0
        self._progress_direction = 1
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._progress_timer.start()
        self._close_on_success = close_on_success

        self._active_worker = BackendWorker(target, *args, **kwargs)
        self._active_worker.status_signal.connect(self._on_status_update)
        self._active_worker.finished_signal.connect(self._on_backend_finished)
        self._active_worker.start()

    def _animate_progress(self):
        # Bounces the fill back and forth to read as "busy", since we
        # don't know how far through the backend steps we are.
        self._progress_value += self._progress_direction * 3
        if self._progress_value >= 100:
            self._progress_value = 100
            self._progress_direction = -1
        elif self._progress_value <= 0:
            self._progress_value = 0
            self._progress_direction = 1
        self.progress_bar.setValue(self._progress_value)

    def _on_status_update(self, message):
        # Runs on the GUI thread (Qt queues the cross-thread signal for us).
        self.status_label.setText(message.strip())

    def _on_backend_finished(self, success, error_message):
        self._set_buttons_enabled(True)
        self._active_worker = None
        self._progress_timer.stop()
        self.progress_bar.hide()

        if not success:
            self.status_label.setText("")
            QMessageBox.critical(self, "Error", error_message or "Operation failed.")
            return
        # On success, leave the label showing the last status message
        # the backend reported (e.g. "GUI launched successfully.").

        if self._close_on_success:
            # Give the user a moment to see the final status message
            # before the launcher hands off to the real app and quits.
            QTimer.singleShot(1200, self.close)

    def _on_launch_clicked(self):
        self._run_backend(launch, "Launching Apple Music...", close_on_success=True)

    def _on_refresh_clicked(self):
        dialog = LoginDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._run_backend(
            refresh_login, "Refreshing login...", dialog.email, dialog.password
        )

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

    try:
        load_config()
    except LauncherError as e:
        QMessageBox.critical(None, "Configuration Error", str(e))
        sys.exit(1)

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()