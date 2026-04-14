import os

from gi.repository import Gdk, GdkPixbuf, Gtk

from disk_overview.utils.helpers import detect_os_id, format_bytes
from disk_overview.utils.icons import icon_for_type


class DiskItem(Gtk.EventBox):
    def __init__(self, mount, on_open, open_in_new_window):
        super().__init__()
        self.mount = mount
        self.on_open = on_open
        self.open_in_new_window = open_in_new_window
        self.set_visible_window(True)
        self.set_hexpand(True)
        self.set_size_request(200, -1)

        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("button-press-event", self._on_click)
        self.connect("enter-notify-event", self._on_hover_enter)
        self.connect("leave-notify-event", self._on_hover_leave)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.box.set_hexpand(True)
        self.box.set_margin_top(6)
        self.box.set_margin_bottom(6)
        self.box.set_margin_start(8)
        self.box.set_margin_end(8)
        self.add(self.box)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.icon_overlay = Gtk.Overlay()
        self.icon = Gtk.Image()
        self.icon_overlay.add(self.icon)
        self.os_badge = Gtk.Image()
        self.os_badge.set_pixel_size(18)
        self.os_badge_box = None
        header.pack_start(self.icon_overlay, False, False, 0)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.title = Gtk.Label(label="", xalign=0)
        self.title.get_style_context().add_class("disk-title")
        self.subtitle = Gtk.Label(label="", xalign=0)
        self.subtitle.get_style_context().add_class("disk-subtitle")
        text_box.pack_start(self.title, False, False, 0)
        text_box.pack_start(self.subtitle, False, False, 0)
        header.pack_start(text_box, True, True, 0)

        self.box.pack_start(header, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(False)
        self.progress.set_hexpand(True)
        self.box.pack_start(self.progress, False, False, 0)

        self.usage_label = Gtk.Label(label="", xalign=0)
        self.usage_label.get_style_context().add_class("disk-usage")
        self.box.pack_start(self.usage_label, False, False, 0)

        self.get_style_context().add_class("disk-item")
        self._os_icon_name = self._resolve_os_icon()
        self.update(mount)

    def update(self, mount):
        self.mount = mount
        name = mount.get("label") or mount.get("name") or mount.get("mountpoint")
        if not name:
            name = mount.get("device", "Dispositivo")

        mountpoint = mount.get("mountpoint", "")
        device = mount.get("device", "")
        self.title.set_text(name)

        subtitle = mountpoint
        if mount.get("type") == "network" and device:
            subtitle = self._format_network_subtitle(device, mountpoint)
        self.subtitle.set_text(subtitle)

        percent = max(0, min(100, int(mount.get("percent", 0))))
        self.progress.set_fraction(percent / 100.0)
        self._apply_usage_class(percent)

        free_bytes = mount.get("free", 0)
        total_bytes = mount.get("total", 0)
        free = format_bytes(free_bytes)
        total = format_bytes(total_bytes)
        free_pct = (free_bytes / total_bytes * 100) if total_bytes > 0 else 0
        self.usage_label.set_text(f"{free} livres ({free_pct:.0f}%) de {total}")

        self._set_icon(icon_for_type(mount.get("type")))
        self._update_os_badge(mount)

    def _apply_usage_class(self, percent):
        context = self.progress.get_style_context()
        context.remove_class("usage-normal")
        context.remove_class("usage-warning")
        context.remove_class("usage-critical")
        if percent >= 90:
            context.add_class("usage-critical")
        elif percent >= 70:
            context.add_class("usage-warning")
        else:
            context.add_class("usage-normal")

    def _on_click(self, _widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_open(self.mount.get("mountpoint"))
            return True
        if event.button == 1:
            self.on_open(self.mount.get("mountpoint"))
            return True
        if event.button == 2:
            self.open_in_new_window(self.mount.get("mountpoint"))
            return True
        return False

    def _on_hover_enter(self, *_args):
        self.get_style_context().add_class("disk-item-hover")
        self.icon.get_style_context().add_class("disk-icon-hover")

    def _on_hover_leave(self, *_args):
        self.get_style_context().remove_class("disk-item-hover")
        self.icon.get_style_context().remove_class("disk-icon-hover")

    @staticmethod
    def _format_network_subtitle(device, mountpoint):
        if not device or not mountpoint:
            return mountpoint or device
        if device.startswith("//"):
            server = device.split("/", 3)
            if len(server) >= 3:
                host = server[2]
                return f"//{host}{mountpoint}"
        return f"{device} -> {mountpoint}"

    def _set_icon(self, icon_value):
        if not icon_value:
            return
        if icon_value.startswith("/") and os.path.exists(icon_value):
            pixbuf = self._load_scaled_pixbuf(icon_value, 48)
            if pixbuf:
                self.icon.set_from_pixbuf(pixbuf)
            else:
                self.icon.set_from_file(icon_value)
            return
        self.icon.set_from_icon_name(icon_value, Gtk.IconSize.DIALOG)

    @staticmethod
    def _load_scaled_pixbuf(path, size):
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(
                path, size, size, True
            )
        except Exception:
            return None


    def _resolve_os_icon(self):
        theme = Gtk.IconTheme.get_default()
        os_id = detect_os_id() or ""
        candidates = []
        if os_id:
            candidates.extend(
                [
                    f"distributor-logo-{os_id}",
                    f"{os_id}-logo",
                    f"{os_id}-icon",
                    os_id,
                ]
            )
        candidates.extend(["distributor-logo", "start-here"])
        for name in candidates:
            if theme.has_icon(name):
                return name
        return None

    def _update_os_badge(self, mount):
        if mount.get("mountpoint") != "/" or not self._os_icon_name:
            if self.os_badge_box is not None:
                self.os_badge_box.hide()
            return
        if self.os_badge_box is None:
            self.os_badge_box = Gtk.EventBox()
            self.os_badge_box.set_visible_window(True)
            self.os_badge_box.get_style_context().add_class("os-badge")
            self.os_badge_box.add(self.os_badge)
            self.os_badge_box.set_halign(Gtk.Align.START)
            self.os_badge_box.set_valign(Gtk.Align.START)
            self.os_badge_box.set_margin_top(-4)
            self.os_badge_box.set_margin_start(-4)
            self.icon_overlay.add_overlay(self.os_badge_box)
        self.os_badge.set_from_icon_name(self._os_icon_name, Gtk.IconSize.MENU)
        self.os_badge_box.show()
