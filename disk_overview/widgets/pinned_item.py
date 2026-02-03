from gi.repository import Gdk, Gtk, Pango


class PinnedItem(Gtk.ListBoxRow):
    def __init__(self, label, path, on_open, on_open_new, on_open_terminal, on_remove=None):
        super().__init__()
        self.label = label
        self.path = path
        self.on_open = on_open
        self.on_open_new = on_open_new
        self.on_open_terminal = on_open_terminal
        self.on_remove = on_remove

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._on_button_press)

        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(6)
        container.set_margin_bottom(6)

        icon = Gtk.Image.new_from_icon_name("folder", Gtk.IconSize.MENU)
        container.pack_start(icon, False, False, 0)

        label_widget = Gtk.Label(label=label, xalign=0)
        label_widget.set_ellipsize(Pango.EllipsizeMode.END)
        container.pack_start(label_widget, True, True, 0)
        self.add(container)

    def _on_button_press(self, _widget, event):
        if event.button == 3:
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event):
        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Abrir")
        open_item.connect("activate", lambda *_: self.on_open(self.path))
        menu.append(open_item)

        new_window_item = Gtk.MenuItem(label="Abrir em nova janela")
        new_window_item.connect("activate", lambda *_: self.on_open_new(self.path))
        menu.append(new_window_item)

        terminal_item = Gtk.MenuItem(label="Abrir terminal aqui")
        terminal_item.connect("activate", lambda *_: self.on_open_terminal(self.path))
        menu.append(terminal_item)

        if self.on_remove is not None:
            remove_item = Gtk.MenuItem(label="Remover dos fixados")
            remove_item.connect("activate", lambda *_: self.on_remove(self.path))
            menu.append(remove_item)

        menu.show_all()
        menu.popup_at_pointer(event)
