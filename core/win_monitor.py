import ctypes, ctypes.wintypes

user32  = ctypes.windll.user32
shell32 = ctypes.windll.shell32

class RECT(ctypes.Structure):
    _fields_ = [("left",ctypes.c_long),("top",ctypes.c_long),
                ("right",ctypes.c_long),("bottom",ctypes.c_long)]

class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize",ctypes.c_uint),("hWnd",ctypes.wintypes.HWND),
                ("uCallbackMessage",ctypes.c_uint),("uEdge",ctypes.c_uint),
                ("rc",RECT),("lParam",ctypes.c_long)]

ABM_GETTASKBARPOS = 0x00000005

def _taskbar_rect() -> RECT:
    d = APPBARDATA(); d.cbSize = ctypes.sizeof(APPBARDATA)
    shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(d))
    return d.rc

def _win_rect(hwnd) -> RECT:
    r = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r)); return r

def _title(hwnd) -> str:
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, b, 256); return b.value

def _primary():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


class WindowMonitor:
    """
    Polled ~120ms. Exposes:
      floor_y          — pixel y where stickman feet should rest
      target_x         — horizontal center to walk toward
      taskbar_top      — top edge of taskbar (y)
      fullscreen_active
      window_moved
      active_title
    """
    def __init__(self):
        self.scr_w, self.scr_h = _primary()
        tb = _taskbar_rect()
        self.taskbar_top  = float(tb.top)
        self.taskbar_h    = float(tb.bottom - tb.top)
        self.taskbar_cx   = float((tb.left + tb.right) // 2)

        self.floor_y           = self.taskbar_top
        self.target_x          = float(self.scr_w // 2)
        self.fullscreen_active = False
        self.window_moved      = False
        self.active_title      = ""
        self._prev_rect        = None
        self._prev_hwnd        = None

    def poll(self):
        
        tb = _taskbar_rect()
        self.taskbar_top = float(tb.top)
        self.taskbar_h   = float(tb.bottom - tb.top)
        self.taskbar_cx  = float((tb.left + tb.right) // 2)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            self.floor_y  = self.taskbar_top
            self.target_x = self.taskbar_cx
            return

        self.active_title = _title(hwnd)
        rect  = _win_rect(hwnd)
        win_w = rect.right  - rect.left
        win_h = rect.bottom - rect.top

        
        self.fullscreen_active = (
            rect.left <= 0 and rect.top <= 0 and
            rect.right >= self.scr_w and rect.bottom >= self.scr_h
        )

        
        if self._prev_hwnd == hwnd and self._prev_rect:
            p = self._prev_rect
            self.window_moved = (p.left != rect.left or p.top != rect.top)
        else:
            self.window_moved = False
        self._prev_hwnd = hwnd
        self._prev_rect = rect

        if self.fullscreen_active:
            
            self.floor_y  = self.taskbar_top
            self.target_x = self.taskbar_cx
        elif win_w > 0 and win_h > 0:
            
            
            raw = float(rect.top) - 48.0
            
            self.floor_y  = max(40.0, min(self.taskbar_top, raw))
            self.target_x = float(rect.left + win_w // 2)
        else:
            self.floor_y  = self.taskbar_top
            self.target_x = self.taskbar_cx

    def notif_pos(self):
        """Bottom-right corner where toast notifications pop."""
        return float(self.scr_w - 100), self.taskbar_top - 8.0
