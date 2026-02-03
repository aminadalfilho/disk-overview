from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ICON_PATHS = {
    "local": BASE_DIR / "data" / "icons" / "hdd.png",
    "removable": BASE_DIR / "data" / "icons" / "hdd.png",
}

ICON_MAP = {
    "local": "drive-harddisk",
    "network": "network-server",
    "removable": "drive-removable-media",
}


def icon_for_type(device_type):
    path = ICON_PATHS.get(device_type)
    if path and path.exists():
        return str(path)
    return ICON_MAP.get(device_type, "drive-harddisk")
