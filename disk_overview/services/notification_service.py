"""Serviço de notificações para alertas de disco cheio."""

import time
from typing import Callable, Optional

import gi

gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gio, Gtk


class NotificationService:
    """Gerencia notificações de disco cheio com cooldown e thresholds configuráveis."""

    def __init__(self, app: Gtk.Application, config_manager, disk_service):
        self.app = app
        self.config_manager = config_manager
        self.disk_service = disk_service
        self._last_notification: dict[str, float] = {}
        self._on_open_folder: Optional[Callable] = None

    def set_open_folder_callback(self, callback: Callable):
        """Define callback para abrir pasta quando usuário clica na notificação."""
        self._on_open_folder = callback

    def _get_config(self) -> dict:
        """Retorna configuração de notificações com valores padrão."""
        defaults = {
            "enabled": True,
            "warning_threshold": 70,
            "critical_threshold": 90,
            "cooldown_seconds": 1800,
            "custom_thresholds": {},
            "ignored_mounts": [],
        }
        config = self.config_manager.get("notifications", {})
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        return config

    def _get_threshold_for_mount(self, mountpoint: str) -> tuple[int, int]:
        """Retorna thresholds (warning, critical) para um mountpoint específico."""
        config = self._get_config()
        custom = config.get("custom_thresholds", {})
        if mountpoint in custom:
            threshold = custom[mountpoint]
            return (
                threshold.get("warning", config["warning_threshold"]),
                threshold.get("critical", config["critical_threshold"]),
            )
        return config["warning_threshold"], config["critical_threshold"]

    def _is_in_cooldown(self, mountpoint: str) -> bool:
        """Verifica se mountpoint está em período de cooldown."""
        config = self._get_config()
        cooldown = config.get("cooldown_seconds", 1800)
        last_time = self._last_notification.get(mountpoint, 0)
        return (time.time() - last_time) < cooldown

    def _update_cooldown(self, mountpoint: str):
        """Atualiza timestamp de última notificação."""
        self._last_notification[mountpoint] = time.time()

    def _is_ignored(self, mountpoint: str) -> bool:
        """Verifica se mountpoint está na lista de ignorados."""
        config = self._get_config()
        return mountpoint in config.get("ignored_mounts", [])

    def add_to_ignored(self, mountpoint: str):
        """Adiciona mountpoint à lista de ignorados e salva config."""
        config = self._get_config()
        if mountpoint not in config["ignored_mounts"]:
            config["ignored_mounts"].append(mountpoint)
            self.config_manager.config["notifications"] = config
            self.config_manager.save()

    def remove_from_ignored(self, mountpoint: str):
        """Remove mountpoint da lista de ignorados."""
        config = self._get_config()
        if mountpoint in config["ignored_mounts"]:
            config["ignored_mounts"].remove(mountpoint)
            self.config_manager.config["notifications"] = config
            self.config_manager.save()

    def _send_notification(self, title: str, body: str, mountpoint: str, is_critical: bool):
        """Envia notificação via Gio.Notification."""
        notification = Gio.Notification.new(title)
        notification.set_body(body)

        if is_critical:
            notification.set_priority(Gio.NotificationPriority.URGENT)
            notification.set_icon(Gio.ThemedIcon.new("dialog-warning"))
        else:
            notification.set_priority(Gio.NotificationPriority.NORMAL)
            notification.set_icon(Gio.ThemedIcon.new("drive-harddisk"))

        # Ação para abrir pasta
        notification.add_button(
            "Abrir pasta",
            f"app.open-folder::{mountpoint}"
        )

        # Ação para ignorar
        notification.add_button(
            "Ignorar",
            f"app.ignore-mount::{mountpoint}"
        )

        # ID único para poder atualizar/substituir notificação do mesmo disco
        notification_id = f"disk-space-{mountpoint.replace('/', '-')}"
        self.app.send_notification(notification_id, notification)
        self._update_cooldown(mountpoint)

    def check_and_notify(self):
        """Verifica todos os discos e envia notificações se necessário."""
        config = self._get_config()
        if not config.get("enabled", True):
            return

        mounts = self.disk_service.list_mounts()

        for mount in mounts:
            mountpoint = mount.get("mountpoint", "")
            percent = mount.get("percent", 0)

            if self._is_ignored(mountpoint):
                continue

            if self._is_in_cooldown(mountpoint):
                continue

            warning_threshold, critical_threshold = self._get_threshold_for_mount(mountpoint)
            label = self.disk_service.get_label(mount)

            if percent >= critical_threshold:
                self._send_notification(
                    f"Disco {label} quase cheio!",
                    f"O disco '{label}' ({mountpoint}) está {percent:.0f}% cheio. "
                    f"Apenas {self._format_size(mount.get('free', 0))} restantes.",
                    mountpoint,
                    is_critical=True,
                )
            elif percent >= warning_threshold:
                self._send_notification(
                    f"Aviso: Disco {label}",
                    f"O disco '{label}' ({mountpoint}) está {percent:.0f}% cheio. "
                    f"Restam {self._format_size(mount.get('free', 0))}.",
                    mountpoint,
                    is_critical=False,
                )

    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para string legível."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
