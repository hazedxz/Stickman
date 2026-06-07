import json, os, copy
from core.constants import DEFAULT_TEXTS

_PATH = os.path.join(os.path.dirname(__file__), "..", "settings.json")

_DEF = {
    "texts":           copy.deepcopy(DEFAULT_TEXTS),
    "idle_warn_sec":   20,   "idle_sleep_sec":  45,
    "cpu_warn_pct":    60,   "cpu_hamster_pct": 80,
    "ram_warn_pct":    80,
    "gravity":         0.90, "walk_speed":      3.6,
    "run_speed":       8.5,
    "notifications":   True, "fullscreen_rage": True,
    "drag_enabled":    True, "bubble_enabled":  True,
    "cpu_reactions":   True, "ram_reactions":   True,
    "cleanup_enabled": True,
}

class Settings:
    def __init__(self):
        self._d = copy.deepcopy(_DEF)
        self.load()

    def load(self):
        p = os.path.abspath(_PATH)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._merge(self._d, json.load(f))
            except Exception:
                pass

    def save(self):
        try:
            with open(os.path.abspath(_PATH), "w", encoding="utf-8") as f:
                json.dump(self._d, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _merge(self, b, o):
        for k, v in o.items():
            if k in b and isinstance(b[k], dict) and isinstance(v, dict):
                self._merge(b[k], v)
            else:
                b[k] = v

    def get(self, k, default=None): return self._d.get(k, default)
    def set(self, k, v): self._d[k] = v; self.save()
    def texts(self, cat): return self._d["texts"].get(cat, ["..."])
    def set_texts(self, cat, lst): self._d["texts"][cat] = lst; self.save()
    def reset_texts(self, cat):
        self._d["texts"][cat] = copy.deepcopy(DEFAULT_TEXTS.get(cat, [])); self.save()
    def reset_all(self): self._d = copy.deepcopy(_DEF); self.save()

    @property
    def idle_warn(self):       return self._d["idle_warn_sec"]
    @property
    def idle_sleep(self):      return self._d["idle_sleep_sec"]
    @property
    def gravity(self):         return self._d["gravity"]
    @property
    def walk_speed(self):      return self._d["walk_speed"]
    @property
    def run_speed(self):       return self._d["run_speed"]
    @property
    def notifications(self):   return self._d["notifications"]
    @property
    def fullscreen_rage(self):  return self._d["fullscreen_rage"]
    @property
    def drag_enabled(self):    return self._d["drag_enabled"]
    @property
    def bubble_enabled(self):  return self._d["bubble_enabled"]
    @property
    def cpu_reactions(self):   return self._d["cpu_reactions"]
    @property
    def ram_reactions(self):   return self._d["ram_reactions"]
    @property
    def cpu_warn_pct(self):    return self._d["cpu_warn_pct"]
    @property
    def cpu_hamster_pct(self): return self._d["cpu_hamster_pct"]
    @property
    def ram_warn_pct(self):    return self._d["ram_warn_pct"]
    @property
    def cleanup_enabled(self): return self._d["cleanup_enabled"]

cfg = Settings()
