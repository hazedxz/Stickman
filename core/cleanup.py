# core/cleanup.py
import os, subprocess, threading, tempfile

def _human(b):
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def _scan():
    dirs = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get("WINDIR","C:\\Windows"), "Temp"),
        os.path.join(os.environ.get("WINDIR","C:\\Windows"), "Prefetch"),
    ]
    count = size = 0
    for d in dirs:
        if not os.path.isdir(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    size  += os.path.getsize(fp)
                    count += 1
                except (PermissionError, OSError):
                    pass
    return count, size

def run_cleanup(bat_path: str, callback):
    """
    callback(count: int, size_str: str) called when done.
    Runs silently — no terminal window.
    """
    def _work():
        count, raw = _scan()
        try:
            subprocess.run(
                ["cmd.exe", "/c", bat_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=60
            )
        except Exception:
            pass
        callback(count, _human(raw))
    threading.Thread(target=_work, daemon=True).start()
