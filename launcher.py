import sys
import json
from pathlib import Path

config_path = Path(__file__).parent / "config.json"

with open(config_path, 'r') as f:
    config = json.load(f)
    
if config["gui_path"] == "":
        print("GUI path is not configured !")
        sys.exit()


