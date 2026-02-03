from gi.repository import GLib, Gtk

from disk_overview.widgets.disk_panel import DiskPanel
from disk_overview.widgets.sidebar import Sidebar


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app, config_manager, disk_service, on_open, on_open_new, on_open_terminal):
        super().__init__(application=app)
        self.config_manager = config_manager
        self.disk_service = disk_service
        self._save_source_id = None

        self.set_title("Disk Overview")
        self.set_default_size(
            config_manager.get("window", {}).get("width", 900),
            config_manager.get("window", {}).get("height", 600),
        )

        if config_manager.get("window", {}).get("remember_position", True):
            last_x = config_manager.get("window", {}).get("last_x", 100)
            last_y = config_manager.get("window", {}).get("last_y", 100)
            self.move(last_x, last_y)

        self.connect("delete-event", self._on_delete)
        self.connect("configure-event", self._on_configure)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.connect("notify::position", self._on_paned_position_changed)
        self.paned = paned

        self.sidebar = Sidebar(config_manager, on_open, on_open_new, on_open_terminal)
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.add(self.sidebar)
        paned.pack1(sidebar_scroll, resize=False, shrink=False)

        self.disk_panel = DiskPanel(on_open, on_open_new)
        panel_scroll = Gtk.ScrolledWindow()
        panel_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        panel_scroll.add(self.disk_panel)
        paned.pack2(panel_scroll, resize=True, shrink=False)

        self.add(paned)
        window_config = self.config_manager.get("window", {})
        sidebar_width = window_config.get("sidebar_width")
        if sidebar_width:
            paned.set_position(sidebar_width)

    def refresh(self):
        local, removable, network = self.disk_service.classify_mounts()
        self.disk_panel.update_mounts(local, removable, network, self.disk_service.get_label)

    def _on_delete(self, *_args):
        window_config = self.config_manager.get("window", {})
        if window_config.get("remember_position", True):
            width, height = self.get_size()
            x, y = self.get_position()
            window_config.update({
                "width": width,
                "height": height,
                "last_x": x,
                "last_y": y,
            })
            self.config_manager.config["window"] = window_config
            self._schedule_save()
        return False

    def _on_configure(self, *_args):
        window_config = self.config_manager.get("window", {})
        if not window_config.get("remember_position", True):
            return False
        width, height = self.get_size()
        x, y = self.get_position()
        window_config.update({
            "width": width,
            "height": height,
            "last_x": x,
            "last_y": y,
        })
        self.config_manager.config["window"] = window_config
        self._schedule_save()
        return False

    def _persist_window_state(self):
        self.config_manager.save()
        self._save_source_id = None
        return False

    def _on_paned_position_changed(self, *_args):
        window_config = self.config_manager.get("window", {})
        window_config["sidebar_width"] = self.paned.get_position()
        self.config_manager.config["window"] = window_config
        self._schedule_save()

    def _schedule_save(self):
        if self._save_source_id is not None:
            GLib.source_remove(self._save_source_id)
        self._save_source_id = GLib.timeout_add(300, self._persist_window_state)
