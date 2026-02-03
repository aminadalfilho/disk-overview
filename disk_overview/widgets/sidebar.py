import os
import urllib.parse

from gi.repository import Gdk, GLib, Gtk

from disk_overview.utils.helpers import user_dir_or_home
from disk_overview.widgets.pinned_item import PinnedItem


class Sidebar(Gtk.Box):
    def __init__(self, config_manager, on_open, on_open_new, on_open_terminal):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.config_manager = config_manager
        self.on_open = on_open
        self.on_open_new = on_open_new
        self.on_open_terminal = on_open_terminal

        self.set_size_request(190, -1)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)

        quick_label = Gtk.Label(label="ACESSO RAPIDO", xalign=0)
        quick_label.get_style_context().add_class("sidebar-section")
        self.pack_start(quick_label, False, False, 0)

        self.quick_list = Gtk.ListBox()
        self.quick_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.quick_list.set_activate_on_single_click(True)
        self.quick_list.connect("row-activated", self._on_row_activated)
        self.pack_start(self.quick_list, False, False, 0)

        pinned_label = Gtk.Label(label="FIXADOS", xalign=0)
        pinned_label.get_style_context().add_class("sidebar-section")
        self.pack_start(pinned_label, False, False, 0)

        self.pinned_list = Gtk.ListBox()
        self.pinned_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pinned_list.set_activate_on_single_click(True)
        self.pinned_list.connect("row-activated", self._on_row_activated)
        self.pinned_list.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [
                Gtk.TargetEntry.new("text/uri-list", 0, 0),
                Gtk.TargetEntry.new("application/x-disk-overview-pinned", Gtk.TargetFlags.SAME_APP, 1),
            ],
            Gdk.DragAction.COPY | Gdk.DragAction.MOVE,
        )
        self.pinned_list.connect("drag-data-received", self._on_pinned_drag_received)
        self.pack_start(self.pinned_list, True, True, 0)

        add_button = Gtk.Button(label="+ Adicionar")
        add_button.connect("clicked", self._on_add_clicked)
        self.pack_start(add_button, False, False, 0)

        self._build_quick_access()
        self.refresh_pinned()

    def _build_quick_access(self):
        entries = [
            ("Pasta pessoal", user_dir_or_home(str(GLib.get_home_dir()))),
            ("Area de trabalho", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP))),
            ("Documentos", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS))),
            ("Downloads", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD))),
            ("Imagens", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES))),
            ("Musicas", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC))),
            ("Videos", user_dir_or_home(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS))),
        ]

        for label, path in entries:
            if not path or not os.path.isdir(path):
                continue
            row = PinnedItem(label, path, self.on_open, self.on_open_new, self.on_open_terminal)
            self.quick_list.add(row)
        self.quick_list.show_all()

    def refresh_pinned(self):
        for child in self.pinned_list.get_children():
            self.pinned_list.remove(child)

        for path in self.config_manager.get("pinned_folders", []):
            label = os.path.basename(path) or path
            row = PinnedItem(
                label,
                path,
                self.on_open,
                self.on_open_new,
                self.on_open_terminal,
                on_remove=self._remove_pinned,
            )
            self._setup_drag_source(row)
            self.pinned_list.add(row)
        self.pinned_list.show_all()

    def _setup_drag_source(self, row):
        row.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            [Gtk.TargetEntry.new("application/x-disk-overview-pinned", Gtk.TargetFlags.SAME_APP, 1)],
            Gdk.DragAction.MOVE,
        )
        row.connect("drag-data-get", self._on_drag_data_get)

    def _on_drag_data_get(self, row, _context, data, _info, _time):
        data.set_text(row.path, -1)

    def _on_pinned_drag_received(self, _widget, _context, x, y, data, info, _time):
        if info == 0:
            self._handle_external_drop(data)
            return

        dragged_path = data.get_text()
        if not dragged_path:
            return
        rows = self.pinned_list.get_children()
        target_row = self.pinned_list.get_row_at_y(y)
        if target_row is None:
            target_index = len(rows)
        else:
            target_index = rows.index(target_row)
        self._reorder_pinned(dragged_path, target_index)

    def _handle_external_drop(self, data):
        uris = data.get_uris()
        if not uris:
            text = data.get_text()
            if text:
                uris = text.splitlines()
        for uri in uris:
            path = urllib.parse.unquote(uri.replace("file://", ""))
            if os.path.isdir(path):
                self.config_manager.add_pinned(path)
        self.refresh_pinned()

    def _reorder_pinned(self, dragged_path, target_index):
        pinned = self.config_manager.get("pinned_folders", [])
        if dragged_path not in pinned:
            return
        new_list = [p for p in pinned if p != dragged_path]
        target_index = max(0, min(target_index, len(new_list)))
        new_list.insert(target_index, dragged_path)
        self.config_manager.reorder_pinned(new_list)
        self.refresh_pinned()

    def _remove_pinned(self, path):
        self.config_manager.remove_pinned(path)
        self.refresh_pinned()

    def _on_row_activated(self, _listbox, row):
        if isinstance(row, PinnedItem):
            self.on_open(row.path)

    def _on_add_clicked(self, _button):
        dialog = Gtk.FileChooserDialog(
            title="Adicionar pasta",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=("Cancelar", Gtk.ResponseType.CANCEL, "Adicionar", Gtk.ResponseType.OK),
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            if folder:
                self.config_manager.add_pinned(folder)
                self.refresh_pinned()
        dialog.destroy()
