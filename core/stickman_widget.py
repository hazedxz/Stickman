# core/stickman_widget.py
import math, random, time, os
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore    import Qt, QTimer
from PyQt5.QtGui     import QPainter

from core.constants  import *
from core.settings   import cfg
from core.renderer   import draw_frame
from core.win_monitor import WindowMonitor
from core.sys_monitor import SysMonitor
from core.cleanup    import run_cleanup

try:
    from pynput import keyboard as kb, mouse as ms
    _PYNPUT = True
except ImportError:
    _PYNPUT = False

import ctypes
user32 = ctypes.windll.user32


class StickmanWidget(QWidget):
    def __init__(self, bat_path: str = ""):
        super().__init__()
        self._bat = bat_path
        self._monitor    = WindowMonitor()
        self._sys        = SysMonitor()

        sw = self._monitor.scr_w
        sh = self._monitor.scr_h

        # ── Transparent overlay ───────────────────────────────
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.Tool | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setGeometry(0, 0, sw, sh)

        # ── Physics ───────────────────────────────────────────
        self.px  = float(sw // 2)
        self.py  = 0.0
        self.vx  = 0.0
        self.vy  = 0.0

        # ── State ─────────────────────────────────────────────
        self.state     = ST_FALLING
        self.direction = 1

        self._sp_active  = False
        self._sp_end     = 0.0
        self._sp_last    = 0.0

        # ── Counters ──────────────────────────────────────────
        self._last_key   = 0.0
        self._idle_since = time.time()
        self._backspaces = 0
        self._burst      = 0
        self._burst_ts   = 0.0

        # ── System reaction state ─────────────────────────────
        self._cpu_state   = None   # None / "sweat" / "hamster"
        self._ram_state   = None
        self._cpu_exempt  = False  # dismissed by user click
        self._ram_exempt  = False
        self._last_sys_chk= 0.0

        # ── Cleanup ───────────────────────────────────────────
        self._cleanup_active = False
        self._cleanup_pct    = 0.0
        self._cleanup_result = None   # (count, size_str)

        # ── Bubble ───────────────────────────────────────────
        self._bubble     = ""
        self._bubble_ts  = 0.0
        self._bubble_dur = 2.5

        # ── Sleep / ZZZ ───────────────────────────────────────
        self._zzz_off    = 0.0

        # ── Drag ─────────────────────────────────────────────
        self._dragging   = False
        self._drag_ox    = 0
        self._drag_oy    = 0
        self._drag_wobble= 0.0

        # ── Rage-quit ─────────────────────────────────────────
        self._rage_on    = False

        # ── Landing squash ────────────────────────────────────
        self._land_ts    = 0.0

        # ── Mouse pos ─────────────────────────────────────────
        self.mx = 0; self.my = 0

        # ── Listeners ─────────────────────────────────────────
        if _PYNPUT:
            self._kb = kb.Listener(on_press=self._key_press,
                                   on_release=self._key_rel)
            self._kb.daemon = True; self._kb.start()

            self._ms = ms.Listener(on_move=self._mouse_move,
                                   on_click=self._mouse_click,
                                   on_scroll=self._scroll)
            self._ms.daemon = True; self._ms.start()

        # ── Timers ────────────────────────────────────────────
        self._t(self._loop,      16)    # 60 fps
        self._t(self._poll_win,  130)   # window radar
        self._t(self._idle_chk,  3500)  # idle check

    # ── timer helper ─────────────────────────────────────────
    def _t(self, fn, ms):
        t = QTimer(self); t.timeout.connect(fn); t.start(ms); return t

    # ── special state ────────────────────────────────────────
    def _enter(self, state, dur):
        now = time.time()
        if self._sp_active and now < self._sp_end:
            return False
        if now - self._sp_last < SP_COOLDOWN:
            return False
        self.state = state
        self._sp_active = True
        self._sp_end    = now + dur
        self._sp_last   = now
        return True

    def _say(self, txt, dur=2.4):
        if not cfg.bubble_enabled: return
        self._bubble     = txt
        self._bubble_ts  = time.time()
        self._bubble_dur = dur

    def _on_floor(self):
        return abs(self.py - self._monitor.floor_y) < 4

    # ═══════════════════════════════════════════════════════
    #  KEYBOARD
    # ═══════════════════════════════════════════════════════
    def _key_press(self, key):
        now = time.time()
        self._last_key   = now
        self._idle_since = now
        self._cpu_exempt = False   # resume cpu reactions after typing

        if key == kb.Key.backspace:
            self._backspaces += 1
            if self._backspaces >= 4:
                self._enter(ST_LAUGHING, 2.4)
                self._say(random.choice(cfg.texts("typo")), 2.4)
                self._backspaces = 0
        else:
            self._backspaces = 0

        if now - self._burst_ts < 0.13:
            self._burst += 1
        else:
            self._burst = 1
        self._burst_ts = now
        if self._burst == 22:
            self._enter(ST_DANCING, 3.2)
            self._say(random.choice(cfg.texts("hackerman")), 3.2)

    def _key_rel(self, key): pass

    # ═══════════════════════════════════════════════════════
    #  MOUSE
    # ═══════════════════════════════════════════════════════
    def _mouse_move(self, x, y):
        self.mx = x; self.my = y
        self._idle_since = time.time()
        if self._dragging and cfg.drag_enabled:
            nx = float(x - self._drag_ox)
            ny = float(y - self._drag_oy)
            ny = max(40.0, min(self._monitor.taskbar_top, ny))
            self.px = nx; self.py = ny

    def _mouse_click(self, x, y, button, pressed):
        self._idle_since = time.time()
        if not cfg.drag_enabled: return

        # Dismiss CPU/RAM state if clicked near stickman
        dist = math.hypot(x - self.px, y - self.py)
        if pressed and dist < 55:
            if self.state in (ST_SWEATING, ST_HAMSTER):
                self._cpu_exempt = True
                self._sp_active  = False
                self._say(random.choice(cfg.texts("cpu_sweat")), 2.0)
                return
            if self.state == ST_RAM_PANIC:
                self._ram_exempt = True
                self._sp_active  = False
                self._say(random.choice(cfg.texts("ram_panic")), 2.0)
                return

        if pressed and dist < 42:
            # Start drag
            self._dragging   = True
            self._drag_ox    = int(x - self.px)
            self._drag_oy    = int(y - self.py)
            self._drag_wobble = 9.0
            self._sp_active  = True
            self._sp_end     = time.time() + 9999
            self.state       = ST_DRAGGED
            self._say(random.choice(cfg.texts("drag_drop")), 1.5)
        elif not pressed and self._dragging:
            self._dragging   = False
            self._drag_wobble = 0.0
            self._sp_active  = False
            self.vy = -4.0
            self.vx = random.uniform(-2.5, 2.5)
            self._say(random.choice(cfg.texts("drop")), 1.2)
        elif pressed and dist < 62 and not self._dragging:
            self._enter(ST_SCARED, 1.5)
            self.vx = random.choice([-1,1]) * random.uniform(7,14)
            self.vy = JUMP_F * 0.65
            self._say(random.choice(cfg.texts("click_near")), 1.2)

    def _scroll(self, x, y, dx, dy):
        self._idle_since = time.time()
        if self._on_floor() and not self._sp_active:
            self.vy = max(JUMP_F * 0.45, -abs(dy) * 5.5)
            self._say(random.choice(cfg.texts("scroll")), 0.9)

    # ═══════════════════════════════════════════════════════
    #  WINDOW RADAR
    # ═══════════════════════════════════════════════════════
    def _poll_win(self):
        self._monitor.poll()

        # Fullscreen rage
        if self._monitor.fullscreen_active and cfg.fullscreen_rage and not self._rage_on:
            self._rage_on = True
            self._enter(ST_RAGEQUIT, 4.0)
            self._say(random.choice(cfg.texts("fullscreen")), 3.0)
        elif not self._monitor.fullscreen_active:
            self._rage_on = False

        # Window moved
        if self._monitor.window_moved and self._on_floor() and not self._sp_active:
            self.vy = JUMP_F * 0.38
            self.vx = random.uniform(-3, 3)
            self._say(random.choice(cfg.texts("window_move")), 1.1)

        # CPU / RAM checks
        self._sys_check()

    def _sys_check(self):
        if not cfg.cpu_reactions and not cfg.ram_reactions: return
        cpu = self._sys.cpu
        ram = self._sys.ram

        if cfg.cpu_reactions and not self._cpu_exempt:
            if cpu >= cfg.cpu_hamster_pct:
                if self._cpu_state != "hamster":
                    self._cpu_state = "hamster"
                    self._enter(ST_HAMSTER, 9999)
                    self._say(random.choice(cfg.texts("cpu_hamster")), 3.0)
            elif cpu >= cfg.cpu_warn_pct:
                if self._cpu_state != "sweat":
                    self._cpu_state = "sweat"
                    self._enter(ST_SWEATING, 9999)
                    self._say(random.choice(cfg.texts("cpu_sweat")), 2.5)
            else:
                if self._cpu_state is not None:
                    self._cpu_state = None
                    self._sp_active = False

        if cfg.ram_reactions and not self._ram_exempt:
            if ram >= cfg.ram_warn_pct:
                if self._ram_state != "panic":
                    self._ram_state = "panic"
                    self._enter(ST_RAM_PANIC, 9999)
                    self._say(random.choice(cfg.texts("ram_panic")), 2.8)
            else:
                if self._ram_state is not None:
                    self._ram_state = None
                    self._sp_active = False

    # ═══════════════════════════════════════════════════════
    #  IDLE CHECK
    # ═══════════════════════════════════════════════════════
    def _idle_chk(self):
        idle = time.time() - self._idle_since
        if idle >= cfg.idle_sleep and not self._sp_active:
            self._enter(ST_SLEEPING, 14.0)
        elif idle >= cfg.idle_warn and not self._sp_active:
            self._say(random.choice(cfg.texts("idle")), 3.0)

    # ═══════════════════════════════════════════════════════
    #  CLEANUP TRIGGER
    # ═══════════════════════════════════════════════════════
    def start_cleanup(self):
        if self._cleanup_active or not self._bat: return
        if not cfg.cleanup_enabled: return
        self._cleanup_active = True
        self._cleanup_pct    = 0.0
        self._enter(ST_CLEANUP, 9999)
        self._say("loading up the truck...", 2.0)
        run_cleanup(self._bat, self._on_cleanup_done)

    def _on_cleanup_done(self, count, size_str):
        self._cleanup_result  = (count, size_str)

    # ═══════════════════════════════════════════════════════
    #  MAIN LOOP
    # ═══════════════════════════════════════════════════════
    def _loop(self):
        now = time.time()

        # Expire special
        if self._sp_active and now >= self._sp_end:
            self._sp_active = False

        # Advance ZZZ
        if self.state == ST_SLEEPING:
            self._zzz_off = (self._zzz_off + 0.27) % 46

        # Cleanup animation progress
        if self._cleanup_active:
            self._cleanup_pct = min(self._cleanup_pct + 0.004, 1.0)
            if self._cleanup_result and self._cleanup_pct >= 0.85:
                count, size = self._cleanup_result
                tmpl = random.choice(cfg.texts("cleanup_done"))
                msg  = tmpl.replace("{count}", str(count)).replace("{size}", size)
                self._say(msg, 5.0)
                self._cleanup_result  = None
                self._cleanup_active  = False
                self._sp_active = False
                self._cleanup_pct = 0.0

        if self._dragging:
            self.update(); return

        # Physics
        floor = self._monitor.floor_y
        self.px += self.vx
        self.py += self.vy
        self.vy += cfg.gravity
        self.vx *= FRICTION

        self.px = max(30.0, min(float(self._monitor.scr_w - 30), self.px))

        if self.py >= floor:
            if self.vy > 6:                        # hard landing
                self.state  = ST_LANDING
                self._land_ts = now
            self.py  = floor
            self.vy  = 0.0
        if self.py < 30.0:
            self.py  = 30.0
            self.vy  = abs(self.vy) * BOUNCE_D

        on_floor = self._on_floor()

        # Landing expires after 0.4s
        if self.state == ST_LANDING and (now - self._land_ts) > 0.4:
            self.state = ST_SITTING

        # State machine (only when no special lock)
        if not self._sp_active:
            if not on_floor:
                self.state = ST_FALLING
            else:
                dist   = abs(self.px - self._monitor.target_x)
                typing = (now - self._last_key) < TYPING_GRACE

                if dist > RUN_THRESH:
                    self.state = ST_RUNNING
                    step = RUN_SPD * (1 if self.px < self._monitor.target_x else -1)
                    self.px += step
                    self.direction = 1 if step > 0 else -1
                elif dist > 18:
                    self.state = ST_WALKING
                    step = WALK_SPD * (1 if self.px < self._monitor.target_x else -1)
                    self.px += step
                    self.direction = 1 if step > 0 else -1
                elif typing:
                    self.state = ST_TYPING
                else:
                    self.state = ST_SITTING

        self.update()

    # ═══════════════════════════════════════════════════════
    #  PAINT
    # ═══════════════════════════════════════════════════════
    def paintEvent(self, event):
        p = QPainter(self)
        now = time.time()
        draw_frame(
            painter       = p,
            cx            = int(self.px),
            cy            = int(self.py),
            state         = self.state,
            direction     = self.direction,
            t             = now * 10,
            bubble_text   = self._bubble,
            bubble_elapsed= now - self._bubble_ts,
            bubble_dur    = self._bubble_dur,
            zzz_off       = self._zzz_off,
            drag_wobble   = self._drag_wobble,
            cleanup_pct   = self._cleanup_pct,
        )
        p.end()

    # ═══════════════════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════════════════
    def trigger_dance(self):
        self._enter(ST_DANCING, 4.0)

    def trigger_scare(self):
        self._enter(ST_SCARED, 1.6)
        self.vx = random.choice([-1,1]) * random.uniform(8,15)
        self.vy = JUMP_F * 0.72

    def trigger_notif(self):
        if not cfg.notifications: return
        nx, ny = self._monitor.notif_pos()
        self._monitor.floor_y  = ny
        self._monitor.target_x = nx
        self._enter(ST_NOTIF, 5.0)
        self._say(random.choice(cfg.texts("notif")), 2.5)

    def trigger_cleanup(self):
        self.start_cleanup()

    def stop(self):
        self._sys.stop()
