import json
from pathlib import Path


class ConfigManager:
    CONFIG_DIR = Path.home() / ".config" / "disk-overview"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self, default_path):
        self.default_path = Path(default_path)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self.load()

    def default_config(self):
        if self.default_path.exists():
            return json.loads(self.default_path.read_text())
        return {
            "version": "1.0",
            "pinned_folders": [],
            "refresh_interval_seconds": 30,
            "open_command": "nautilus",
            "terminal_command": "gnome-terminal",
            "keyboard_shortcut": "Super+E",
            "window": {
                "width": 900,
                "height": 600,
                "remember_position": True,
                "last_x": 100,
                "last_y": 100,
                "sidebar_width": 200,
            },
            "appearance": {
                "show_free_space_text": True,
                "bar_color_normal": "#3584e4",
                "bar_color_warning": "#ff7800",
                "bar_color_critical": "#e01b24",
            },
        }

    def load(self):
        if self.CONFIG_FILE.exists():
            return json.loads(self.CONFIG_FILE.read_text())
        config = self.default_config()
        self.save(config)
        return config

    def save(self, config=None):
        if config is not None:
            self.config = config
        self.CONFIG_FILE.write_text(json.dumps(self.config, indent=2))

    def add_pinned(self, path):
        if path not in self.config["pinned_folders"]:
            self.config["pinned_folders"].append(path)
            self.save()

    def remove_pinned(self, path):
        if path in self.config["pinned_folders"]:
            self.config["pinned_folders"].remove(path)
            self.save()

    def reorder_pinned(self, new_list):
        self.config["pinned_folders"] = new_list
        self.save()

    def get(self, key, default=None):
        return self.config.get(key, default)
