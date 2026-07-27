import sys
import json
import subprocess
import time

from pathlib import Path

# Launch Docker Desktop
def start_docker_desktop():

    print("Starting Docker Desktop...")

    try:
        subprocess.run(
            ["/usr/bin/open", "-a", "Docker"],
            check=True
        )

    except FileNotFoundError:
        print("'open' command not found.")
        sys.exit(1)

    except subprocess.CalledProcessError:
        print("Failed to launch Docker Desktop.")
        sys.exit(1)

# Wait for Docker Daemon
def wait_for_docker(timeout=60):

    print("Waiting for Docker...")
    start_time = time.time()

    while True:
        try:
            subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            print("Docker is ready.")
            return

        except subprocess.CalledProcessError:
            pass

        except FileNotFoundError:
            print("Docker CLI not found.")
            sys.exit(1)

        if time.time() - start_time > timeout:
            print("Timed out waiting for Docker.")
            sys.exit(1)

        time.sleep(1)


config_path = Path(__file__).parent / "config.json"

with open(config_path, 'r') as f:
    config = json.load(f)
    
if not config["gui_path"]:
        print("GUI path is not configured !")
        sys.exit()

gui_path = Path(config["gui_path"])

# Check if the path doesn't exist
if not gui_path.exists():
    print("Path doesn't exist !")
    sys.exit()

# Check if the path is not a directory
if not gui_path.is_dir():
    print("GUI path must be a directory")
    sys.exit()

# Check if the path is empty
if not config["wrapper_path"]:
    print("Wrapper path is not configured.")
    sys.exit()

wrapper_path = Path(config["wrapper_path"])

# Check if the path doesn't exist
if not wrapper_path.exists():
    print("Wrapper path doesn't exist.")
    sys.exit()

# Check if the path is not a directory
if not wrapper_path.is_dir():
    print("Wrapper path must be a directory.")
    sys.exit()


def start_wrapper():

    print("Starting wrapper container...")
    wrapper_data = wrapper_path / "rootfs" / "data"
    wrapper_data.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.Popen(
            [
                "docker",
                "run",
                "-v", f"{wrapper_data}:/app/rootfs/data",
                "-p", "10020:10020",
                "-p", "20020:20020",
                "-e", "args=-M 20020 -H 0.0.0.0",
                "--rm",
                "ghcr.io/itouakirai/wrapper:x86"
            ]
        )

    except FileNotFoundError:
        print("Docker CLI not found.")
        sys.exit(1)

start_docker_desktop()
wait_for_docker()
start_wrapper()