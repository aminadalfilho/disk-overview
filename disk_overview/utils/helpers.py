import os
import shlex
import subprocess
from pathlib import Path


def format_bytes(num_bytes):
    if num_bytes is None:
        return "0 B"
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    for unit in units:
        if size < step:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= step
    return f"{size:.1f} EB"


def safe_mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def open_in_file_manager(path, command):
    args = shlex.split(command) if command else ["nautilus"]
    try:
        subprocess.Popen(args + [path])
    except FileNotFoundError:
        subprocess.Popen(["nautilus", path])


def open_in_new_window(path, command):
    args = shlex.split(command) if command else ["nautilus"]
    if args and "nautilus" in args[0]:
        subprocess.Popen(args + ["--new-window", path])
    else:
        subprocess.Popen(args + [path])


def open_terminal_here(path, terminal_command):
    args = shlex.split(terminal_command) if terminal_command else ["gnome-terminal"]
    if args and "gnome-terminal" in args[0]:
        subprocess.Popen(args + [f"--working-directory={path}"])
        return
    try:
        subprocess.Popen(args, cwd=path)
    except FileNotFoundError:
        subprocess.Popen(["gnome-terminal", f"--working-directory={path}"])


def is_removable_mount(mountpoint):
    if not mountpoint:
        return False
    return mountpoint.startswith("/media/") or mountpoint.startswith("/run/media/")


def resolve_path(uri_or_path):
    if uri_or_path.startswith("file://"):
        return uri_or_path.replace("file://", "")
    return uri_or_path


def user_dir_or_home(path):
    if path and os.path.isdir(path):
        return path
    return str(Path.home())


def detect_os_id():
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("ID="):
                    return line.strip().split("=", 1)[1].strip().strip('"')
    except OSError:
        return None
    return None
