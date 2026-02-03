from gi.repository import GLib


class MountMonitor:
    def __init__(self, interval_seconds, callback):
        self.interval_seconds = interval_seconds
        self.callback = callback
        self._source_id = None

    def start(self):
        self.stop()
        self._source_id = GLib.timeout_add_seconds(self.interval_seconds, self._tick)

    def stop(self):
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None

    def _tick(self):
        self.callback()
        return True
