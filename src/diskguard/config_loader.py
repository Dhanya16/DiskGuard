from pathlib import Path
import yaml

_CONFIG_FILE_THRESHOLDS = (
    Path(__file__).parent
    / "config"
    / "thresholds.yaml"
)

_CONFIG_FILE_CONTAINERS = (
    Path(__file__).parent
    / "config"
    / "containers.yaml"
)

with open(_CONFIG_FILE_THRESHOLDS, "r", encoding="utf-8") as f:
    threshold = yaml.safe_load(f)

with open(_CONFIG_FILE_CONTAINERS, "r", encoding="utf-8") as f:
    containers = yaml.safe_load(f)