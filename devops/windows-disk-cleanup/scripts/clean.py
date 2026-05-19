"""
Windows disk cleanup executor.
Cleans specified directories with error handling.
Usage: python clean.py [target1 target2 ...]
Targets: temp_user temp_system logs chrome edge thumbnails pip winupdate recycle downloads
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def fmt_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"

def get_dir_size(p):
    try:
        total = 0
        if os.path.isfile(p):
            return os.path.getsize(p)
        for dirpath, dirnames, filenames in os.walk(str(p)):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except:
                    pass
        return total
    except:
        return 0

def clean_dir(path, name):
    p = Path(path)
    if not p.exists():
        return 0, "not found"

    before = get_dir_size(p)
    if before == 0:
        return 0, "already empty"

    errors = 0
    for item in p.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            else:
                shutil.rmtree(str(item))
        except PermissionError:
            errors += 1
        except Exception:
            errors += 1

    after = get_dir_size(p)
    freed = before - after
    status = "ok" if errors == 0 else f"partial ({errors} locked)"
    return freed, status


home = Path(os.path.expandvars("%USERPROFILE%"))
appdata_local = home / "AppData/Local"

TARGET_MAP = {
    "temp_user": (home / "AppData/Local/Temp", "User Temp"),
    "temp_system": (Path("C:/Windows/Temp"), "System Temp"),
    "logs": (Path("C:/Windows/Logs"), "Windows Logs"),
    "chrome": (appdata_local / "Google/Chrome/User Data/Default/Cache", "Chrome Cache"),
    "edge": (appdata_local / "Microsoft/Edge/User Data/Default/Cache", "Edge Cache"),
    "thumbnails": (home / "AppData/Local/Microsoft/Windows/Explorer", "Thumbnails"),
    "pip": (home / "AppData/Local/pip/cache", "pip Cache"),
    "winupdate": (Path("C:/Windows/SoftwareDistribution/Download"), "Windows Update Cache"),
    "recycle": (None, "Recycle Bin"),  # special
    "downloads": (home / "Downloads", "Downloads"),
}

targets = sys.argv[1:] if len(sys.argv) > 1 else list(TARGET_MAP.keys())

total_freed = 0
for t in targets:
    if t not in TARGET_MAP:
        print(f"  Unknown target: {t}")
        continue
    path, name = TARGET_MAP[t]

    if t == "recycle":
        try:
            r = subprocess.run(
                ['powershell', '-Command', 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'],
                capture_output=True, text=True, timeout=30
            )
            status = "ok" if r.returncode == 0 else "need admin"
        except Exception as e:
            status = f"error: {e}"
        freed = 0
    else:
        freed, status = clean_dir(path, name)

    print(f"  [{status:12}] {name:25s} freed {fmt_size(freed)}")
    total_freed += freed

print(f"\n  Total freed: {fmt_size(total_freed)}")
