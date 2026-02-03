from gi.repository import Gtk

from disk_overview.widgets.disk_item import DiskItem


class DiskPanel(Gtk.Box):
    def __init__(self, on_open, on_open_new):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.on_open = on_open
        self.on_open_new = on_open_new
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)

        self.local_label = Gtk.Label(label="DISPOSITIVOS E UNIDADES", xalign=0)
        self.local_label.get_style_context().add_class("panel-section")
        self.pack_start(self.local_label, False, False, 0)

        self.local_box = Gtk.FlowBox()
        self.local_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.local_box.set_min_children_per_line(1)
        self.local_box.set_max_children_per_line(3)
        self.local_box.set_row_spacing(10)
        self.local_box.set_column_spacing(10)
        self.local_box.set_homogeneous(True)
        self.pack_start(self.local_box, False, False, 0)

        self.network_label = Gtk.Label(label="LOCAIS DE REDE", xalign=0)
        self.network_label.get_style_context().add_class("panel-section")
        self.pack_start(self.network_label, False, False, 0)

        self.network_box = Gtk.FlowBox()
        self.network_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.network_box.set_min_children_per_line(1)
        self.network_box.set_max_children_per_line(3)
        self.network_box.set_row_spacing(10)
        self.network_box.set_column_spacing(10)
        self.network_box.set_homogeneous(True)
        self.pack_start(self.network_box, False, False, 0)

        self.items = {}

    def update_mounts(self, local_mounts, removable_mounts, network_mounts, label_func):
        local_list = local_mounts + removable_mounts
        self._sync_section(self.local_box, local_list, label_func)
        self._sync_section(self.network_box, network_mounts, label_func)

    def _sync_section(self, container, mounts, label_func):
        existing = {}
        for child in container.get_children():
            item = child.get_child()
            if item and hasattr(item, "mount"):
                existing[item.mount.get("mountpoint")] = child
        current = set()
        for mount in mounts:
            mountpoint = mount.get("mountpoint")
            mount["label"] = label_func(mount)
            if mountpoint in existing:
                item = existing[mountpoint].get_child()
                if item:
                    item.update(mount)
            else:
                item = DiskItem(mount, self.on_open, self.on_open_new)
                container.add(item)
            current.add(mountpoint)

        for mountpoint, widget in existing.items():
            if mountpoint not in current:
                container.remove(widget)
        container.show_all()
