---
name: windows-disk-cleanup
description: "Scan and safely clean junk files on Windows C: drive: temp files, browser caches, logs, thumbnails, Recycle Bin. Use when user says C drive full, disk cleanup, or free up space."
---

# Windows Disk Cleanup

Scan C: drive for cleanup candidates, present a ranked list to the user, then execute cleanup on confirmed items.

⚠️ **Permission gate**: NEVER use this skill proactively. Always ask Paradigme for explicit permission before any cleanup action. Present the scan results first and wait for confirmation.

## Workflow

1. **Scan** — Run `scripts/scan.py` to discover cleanup candidates across known junk locations.
2. **Present** — Show results sorted by size with safety ratings (safe / review first).
3. **Confirm** — Let the user choose which items to clean.
4. **Clean** — Run `scripts/clean.py` with the selected items, handling permission errors gracefully.

## Cleanup Targets (Windows)

| Priority | Location | Safety |
|----------|----------|--------|
| High | `%LOCALAPPDATA%\Temp` (user temp) | Always safe |
| High | `C:\Windows\Temp` (system temp) | Safe |
| Medium | `C:\Windows\Logs` | May need admin |
| Medium | Chrome/Edge cache (`User Data\Default\Cache`) | Safe |
| Low | `C:\Windows\SoftwareDistribution\Download` | Safe (Windows Update cache) |
| Low | `%LOCALAPPDATA%\pip\cache` | Safe |
| Low | `%LOCALAPPDATA%\Microsoft\Windows\Explorer` (thumbnails) | Safe |
| Low | `C:\$Recycle.Bin` | Use PowerShell `Clear-RecycleBin -Force` |
| Review | `%USERPROFILE%\Downloads` | User must review first |

## Pitfalls

- **Recycle Bin**: Cannot just `rm -rf C:\$Recycle.Bin`. Must use `powershell -Command "Clear-RecycleBin -Force"`. May require admin.
- **Permissions**: Some temp files may be locked by running processes — this is normal, skip them silently.
- **Admin rights**: `C:\Windows\Temp` and `C:\Windows\Logs` may have protected subdirectories. Handle `PermissionError` gracefully.
- **Browser cache**: Delete while browser is CLOSED to avoid lock errors and data corruption.
- **Do NOT delete `C:\Windows\Prefetch`** — it actually speeds up boot, contrary to popular cleanup advice.

## Scripts

- `scripts/scan.py` — Scans all known junk locations and returns size-ranked results + disk overview.
- `scripts/clean.py` — Cleans specified target directories with error handling and summary.
