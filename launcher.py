import sys
import json
from pathlib import Path

config_path = Path(__file__).parent / "config.json"

with open(config_path, 'r') as f:
    config = json.load(f)
    
if not config["gui_path"]:
        print("GUI path is not configured !")
        sys.exit()

gui_path = Path(config["gui_path"])

#Check if the path doesn't exist
if not gui_path.exists():
    print("Path doesn't exist !")
    sys.exit()

#Check if the path is not a directory
if not gui_path.is_dir():
    print("GUI path must be a directory")
    sys.exit()