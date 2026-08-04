import json
import os
import subprocess
import time
import socket

from pathlib import Path

CONFIG_DIR = Path.home() / "Library" / "Application Support" / "AppleMusicLauncher"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "gui_path": "",
    "wrapper_path": "",
}

# Common locations for the docker CLI on macOS. A .app launched from
# Finder/Dock doesn't go through the user's shell, so it doesn't pick
# up PATH changes from .zshrc/.bash_profile the way a Terminal-run
# script does - "docker" can be found fine from Terminal but raise
# FileNotFoundError from a packaged .app. This lets subprocess find
# it either way without changing any of the actual docker calls.
COMMON_DOCKER_PATHS = [
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/Applications/Docker.app/Contents/Resources/bin",
]


def _ensure_docker_on_path():
    path_entries = os.environ.get("PATH", "").split(os.pathsep)

    for candidate in COMMON_DOCKER_PATHS:
        if candidate not in path_entries and Path(candidate).is_dir():
            path_entries.append(candidate)

    os.environ["PATH"] = os.pathsep.join(path_entries)


# Populated by load_config(). Read by start_gui(), start_wrapper(),
# and login_wrapper() below.
gui_path = None
wrapper_path = None


class LauncherError(Exception):
    """
    Raised when a backend operation fails. This module never exits the
    process itself - it's shared by the CLI (launcher.py) and the GUI
    (gui.py), and each frontend decides how to react to a failure
    (print + sys.exit for the CLI, a QMessageBox for the GUI).
    """
    pass


def report_status(message, status_callback=None):
    """
    Single source of truth for a progress message: always prints it
    (so the CLI output is unchanged), and additionally hands it to
    status_callback if one was provided (so the GUI can display the
    same message without duplicating any strings).
    """
    print(message)
    if status_callback is not None:
        status_callback(message)


def _ensure_config_exists(path):
    """
    Creates the config directory and a default config.json if either
    is missing. The packaged .app is treated as read-only, so this
    lives outside the bundle in ~/Library/Application Support - the
    file is safe to edit and survives app rebuilds/reinstalls.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with open(path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def load_config(config_path=None):
    """
    Load and validate config.json, populating the module-level
    gui_path and wrapper_path used by the rest of this module.

    Must be called once by a frontend before calling launch() or
    refresh_login(). Raises LauncherError if the config is invalid.
    """
    global gui_path, wrapper_path

    _ensure_docker_on_path()

    path = config_path or DEFAULT_CONFIG_PATH

    _ensure_config_exists(path)

    try:
        with open(path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        raise LauncherError("config.json not found.")
    except json.JSONDecodeError:
        raise LauncherError("config.json contains invalid JSON.")

    gui = config.get("gui_path")
    wrapper = config.get("wrapper_path")

    if not gui:
        raise LauncherError("GUI path is not configured.")

    candidate_gui_path = Path(gui)

    # Check if the path doesn't exist
    if not candidate_gui_path.exists():
        raise LauncherError("Path doesn't exist !")

    # Check if the path is not a directory
    if not candidate_gui_path.is_dir():
        raise LauncherError("GUI path must be a directory")

    # Check if the path is empty
    if not wrapper:
        raise LauncherError("Wrapper path is not configured.")

    candidate_wrapper_path = Path(wrapper)

    # Check if the path doesn't exist
    if not candidate_wrapper_path.exists():
        raise LauncherError("Wrapper path doesn't exist.")

    # Check if the path is not a directory
    if not candidate_wrapper_path.is_dir():
        raise LauncherError("Wrapper path must be a directory.")

    gui_path = candidate_gui_path
    wrapper_path = candidate_wrapper_path


# Launch Docker Desktop
def start_docker_desktop(status_callback=None):

    report_status("Starting Docker Desktop...", status_callback)

    try:
        subprocess.run(
            ["/usr/bin/open", "-a", "Docker"],
            check=True
        )

    except FileNotFoundError:
        raise LauncherError("'open' command not found.")

    except subprocess.CalledProcessError:
        raise LauncherError("Failed to launch Docker Desktop.")

# Wait for Docker Daemon
def wait_for_docker(timeout=60, status_callback=None):

    report_status("Waiting for Docker...", status_callback)
    start_time = time.time()

    while True:
        try:
            subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            report_status("Docker is ready.", status_callback)
            return

        except subprocess.CalledProcessError:
            pass

        except FileNotFoundError:
            raise LauncherError("Docker CLI not found.")

        if time.time() - start_time > timeout:
            raise LauncherError("Timed out waiting for Docker.")

        time.sleep(1)


# Helper function
def stop_existing_wrapper():
    subprocess.run(
        [
            "docker",
            "stop",
            "apple-music-wrapper"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def start_wrapper(status_callback=None):

    stop_existing_wrapper()
    report_status("Starting wrapper container...", status_callback)
    wrapper_data = wrapper_path / "rootfs" / "data"
    wrapper_data.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.Popen(
            [
                "docker",
                "run",
                "--name", "apple-music-wrapper",
                "-v", f"{wrapper_data}:/app/rootfs/data",
                "-p", "10020:10020",
                "-p", "20020:20020",
                "-e", "args=-M 20020 -H 0.0.0.0",
                "--rm",
                "ghcr.io/itouakirai/wrapper:x86"
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    except FileNotFoundError:
        raise LauncherError("Docker CLI not found.")

def login_wrapper(email, password, status_callback=None):

    stop_existing_wrapper()

    print("Wrapper Login")
    print()
    wrapper_data = wrapper_path / "rootfs" / "data"
    wrapper_data.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.Popen(
            [
                "docker",
                "run",
                "-d",
                "--name", "apple-music-wrapper",
                "-v", f"{wrapper_data}:/app/rootfs/data",
                "-p", "10020:10020",
                "-p", "20020:20020",
                "-e", f"args=-L {email}:{password} -F",
                "--rm",
                "ghcr.io/itouakirai/wrapper:x86",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        wait_for_wrapper(status_callback=status_callback)
        print("\nLogin completed successfully.")
        return

    except FileNotFoundError:
        raise LauncherError("Docker CLI not found.")

    except LauncherError:
        raise

    except Exception as e:
        raise LauncherError(f"Wrapper login failed: {e}")

def wait_for_wrapper(timeout=30, status_callback=None):

    report_status("Waiting for wrapper...", status_callback)

    start_time = time.time()

    while True:

        try:
            with socket.create_connection(("127.0.0.1", 10020), timeout=1):
                report_status("Wrapper is ready.", status_callback)
                return

        except OSError:
            pass

        if time.time() - start_time > timeout:
            raise LauncherError("Timed out waiting for wrapper.")

        time.sleep(1)

def start_gui(status_callback=None):

    report_status("Starting GUI...", status_callback)

    gui_root = gui_path
    python_executable = gui_root / "venv" / "bin" / "python"
    main_script = gui_root / "src" / "main.py"

    if not python_executable.exists():
        raise LauncherError("Python executable not found in GUI virtual environment.")

    if not main_script.exists():
        raise LauncherError("GUI entry point not found.")

    try:
        subprocess.Popen(
            [str(python_executable), str(main_script)],
            cwd=gui_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    except FileNotFoundError:
        raise LauncherError("Failed to launch GUI.")

def launch(status_callback=None):
    start_docker_desktop(status_callback=status_callback)
    wait_for_docker(status_callback=status_callback)
    start_wrapper(status_callback=status_callback)
    wait_for_wrapper(status_callback=status_callback)
    start_gui(status_callback=status_callback)
    report_status("GUI launched successfully.", status_callback)

def refresh_login(email, password, status_callback=None):
    start_docker_desktop(status_callback=status_callback)
    wait_for_docker(status_callback=status_callback)
    login_wrapper(email, password, status_callback=status_callback)