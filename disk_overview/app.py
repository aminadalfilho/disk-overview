from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gdk, Gio, GLib, Gtk

from disk_overview.services.config import ConfigManager
from disk_overview.services.disk_service import DiskService
from disk_overview.services.mount_monitor import MountMonitor
from disk_overview.services.notification_service import NotificationService
from disk_overview.utils.helpers import open_in_file_manager, open_in_new_window, open_terminal_here
from disk_overview.widgets.main_window import MainWindow


class DiskOverviewApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.linuxexplorer.DiskOverview")
        self.window = None
        self.disk_service = DiskService()
        config_path = Path(__file__).resolve().parent.parent / "config" / "default_config.json"
        self.config_manager = ConfigManager(config_path)
        self.monitor = None
        self.notification_service = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self._load_css()
        self._register_actions()

        # Inicializa serviço de notificações
        self.notification_service = NotificationService(
            self, self.config_manager, self.disk_service
        )
        self.notification_service.set_open_folder_callback(self._open_path)

    def do_activate(self):
        if self.window is None:
            self.window = MainWindow(
                self,
                self.config_manager,
                self.disk_service,
                self._open_path,
                self._open_in_new_window,
                self._open_terminal,
            )
            self._setup_shortcut()

        self.window.show_all()
        self.window.present()
        self.refresh()
        self._start_monitor()

    def _load_css(self):
        css_path = Path(__file__).resolve().parent.parent / "data" / "styles.css"
        if not css_path.exists():
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(str(css_path))
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _register_actions(self):
        """Registra ações GIO para notificações."""
        # Ação: Abrir pasta
        action_open = Gio.SimpleAction.new("open-folder", GLib.VariantType.new("s"))
        action_open.connect("activate", self._on_action_open_folder)
        self.add_action(action_open)

        # Ação: Ignorar mount
        action_ignore = Gio.SimpleAction.new("ignore-mount", GLib.VariantType.new("s"))
        action_ignore.connect("activate", self._on_action_ignore_mount)
        self.add_action(action_ignore)

    def _on_action_open_folder(self, action, parameter):
        """Handler para ação de abrir pasta via notificação."""
        mountpoint = parameter.get_string()
        if mountpoint:
            self._open_path(mountpoint)

    def _on_action_ignore_mount(self, action, parameter):
        """Handler para ação de ignorar mount via notificação."""
        mountpoint = parameter.get_string()
        if mountpoint and self.notification_service:
            self.notification_service.add_to_ignored(mountpoint)

    def _setup_shortcut(self):
        accel = self.config_manager.get("keyboard_shortcut", "Super+E")
        key, mod = Gtk.accelerator_parse(accel)
        if key == 0 and "Super+" in accel:
            normalized = accel.replace("Super+", "<Super>")
            key, mod = Gtk.accelerator_parse(normalized)
        if key == 0:
            return
        accel_group = Gtk.AccelGroup()
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, self._on_shortcut)
        self.window.add_accel_group(accel_group)

    def _on_shortcut(self, *_args):
        if self.window:
            self.window.present()
        return True

    def _start_monitor(self):
        interval = self.config_manager.get("refresh_interval_seconds", 30)
        if self.monitor is None:
            self.monitor = MountMonitor(interval, self.refresh)
        else:
            self.monitor.interval_seconds = interval
        self.monitor.start()

    def refresh(self):
        if self.window:
            self.window.refresh()

        # Verifica notificações
        if self.notification_service:
            self.notification_service.check_and_notify()

    def _open_path(self, path):
        if path:
            open_in_file_manager(path, self.config_manager.get("open_command"))
            if self.window:
                self.window.close()

    def _open_in_new_window(self, path):
        if path:
            open_in_new_window(path, self.config_manager.get("open_command"))

    def _open_terminal(self, path):
        if path:
            open_terminal_here(path, self.config_manager.get("terminal_command"))
