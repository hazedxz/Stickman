import psutil, threading

class SysMonitor:
    def __init__(self):
        self._cpu = 0.0; self._ram = 0.0
        self._lock = threading.Lock(); self._running = True
        psutil.cpu_percent(interval=None)          # prime
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._running:
            c = psutil.cpu_percent(interval=2.8)
            r = psutil.virtual_memory().percent
            with self._lock:
                self._cpu = c; self._ram = r

    @property
    def cpu(self):
        with self._lock: return self._cpu
    @property
    def ram(self):
        with self._lock: return self._ram
    def stop(self): self._running = False
