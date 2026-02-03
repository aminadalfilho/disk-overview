import gi

gi.require_version("Gtk", "3.0")

from disk_overview.app import DiskOverviewApp


def main():
    app = DiskOverviewApp()
    app.run(None)


if __name__ == "__main__":
    main()
