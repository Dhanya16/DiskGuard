from pathlib import Path
import yaml

_CONFIG_FILE = (
    Path(__file__).parent
    / "config"
    / "thresholds.yaml"
)

with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
    threshold = yaml.safe_load(f)