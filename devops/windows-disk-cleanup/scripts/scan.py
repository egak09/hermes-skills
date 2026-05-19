"""
Windows disk cleanup scanner.
Scans common junk locations and prints size-ranked results + disk overview.
"""
import os
import shutil
from pathlib import Path

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

home = Path(os.path.expandvars("%USERPROFILE%"))
appdata_local = home / "AppData/Local"

TARGETS = [
    ("User Temp", home / "AppData/Local/Temp", "safe"),
    ("System Temp", Path("C:/Windows/Temp"), "safe"),
    ("Windows Logs", Path("C:/Windows/Logs"), "caution"),
    ("Chrome Cache", appdata_local / "Google/Chrome/User Data/Default/Cache", "safe"),
    ("Edge Cache", appdata_local / "Microsoft/Edge/User Data/Default/Cache", "safe"),
    ("Thumbnail Cache", home / "AppData/Local/Microsoft/Windows/Explorer", "safe"),
    ("pip Cache", home / "AppData/Local/pip/cache", "safe"),
    ("Windows Update Cache", Path("C:/Windows/SoftwareDistribution/Download"), "safe"),
    ("Recycle Bin", Path("C:/$Recycle.Bin"), "caution"),
    ("Downloads", home / "Downloads", "review"),
]

results = []
for name, path, safety in TARGETS:
    if path.exists():
        s = get_dir_size(path)
        if s > 1024 * 1024:  # > 1 MB
            results.append((name, str(path), s, safety))

results.sort(key=lambda x: -x[2])

total = 0
for name, path, size, safety in results:
    print(f"[{safety:6}] {name:25s}  {fmt_size(size):>10s}    {path}")
    total += size

print(f"\n{'='*60}")
print(f"  Total cleanable: {fmt_size(total)}")
print(f"{'='*60}")

usage = shutil.disk_usage("C:/")
print(f"\nDisk: {fmt_size(usage.used)} / {fmt_size(usage.total)} used ({usage.used/usage.total*100:.1f}%)")
print(f"Free:  {fmt_size(usage.free)} ({usage.free/usage.total*100:.1f}%)")
