import os
from pathlib import Path

import psutil

from disk_overview.utils.helpers import is_removable_mount

LOCAL_FSTYPES = {
    "ext2",
    "ext3",
    "ext4",
    "btrfs",
    "xfs",
    "ntfs",
    "vfat",
    "exfat",
}

NETWORK_FSTYPES = {"cifs", "nfs", "nfs4", "sshfs"}


class DiskService:
    def __init__(self):
        pass

    def _network_mounts(self):
        mounts = []
        try:
            with open("/proc/mounts", "r", encoding="utf-8") as handle:
                for line in handle:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    device, mountpoint, fstype = parts[0], parts[1], parts[2]
                    if fstype in NETWORK_FSTYPES:
                        mounts.append({
                            "type": "network",
                            "device": device,
                            "mountpoint": mountpoint,
                            "fstype": fstype,
                        })
        except OSError:
            return []
        return mounts

    def _disk_usage(self, mountpoint):
        try:
            usage = psutil.disk_usage(mountpoint)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            }
        except (PermissionError, FileNotFoundError, OSError):
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0,
            }

    def list_mounts(self):
        mounts = []

        network_mounts = self._network_mounts()
        network_mountpoints = {m["mountpoint"] for m in network_mounts}
        for mount in network_mounts:
            mount.update(self._disk_usage(mount["mountpoint"]))
            mounts.append(mount)

        for partition in psutil.disk_partitions(all=False):
            if partition.fstype not in LOCAL_FSTYPES:
                continue
            if partition.mountpoint in network_mountpoints:
                continue
            if not os.path.exists(partition.mountpoint):
                continue
            device_type = "removable" if is_removable_mount(partition.mountpoint) else "local"
            usage = self._disk_usage(partition.mountpoint)
            mounts.append({
                "type": device_type,
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                **usage,
            })

        return mounts

    def classify_mounts(self):
        local = []
        removable = []
        network = []
        for mount in self.list_mounts():
            if mount["type"] == "network":
                network.append(mount)
            elif mount["type"] == "removable":
                removable.append(mount)
            else:
                local.append(mount)
        return local, removable, network

    def get_label(self, mount):
        mountpoint = mount.get("mountpoint", "")
        if mountpoint == "/":
            return "Sistema (/)"
        name = Path(mountpoint).name
        return name or mountpoint
