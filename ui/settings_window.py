from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QTextEdit, QPushButton, QCheckBox, QSlider, QGroupBox,
    QScrollArea, QFrame, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont

from core.settings  import cfg
from core.constants import DEFAULT_TEXTS

BG     = "#161616"; BG2 = "#202020"; ACC = "#d2af37"
FG     = "#f0f0f0"; FG2 = "#909090"; BTN = "#2a2a2a"

QSS = f"""
QWidget          {{ background:{BG}; color:{FG}; font:12px 'Consolas',monospace; }}
QTabWidget::pane {{ border:1px solid #2e2e2e; background:{BG2}; }}
QTabBar::tab     {{ background:{BG}; color:{FG2}; padding:6px 18px;
                    border-radius:4px 4px 0 0; }}
QTabBar::tab:selected {{ background:{ACC}; color:#111; font-weight:bold; }}
QGroupBox        {{ border:1px solid #2e2e2e; border-radius:6px;
                    margin-top:10px; padding-top:8px; }}
QGroupBox::title {{ color:{ACC}; subcontrol-origin:margin;
                    left:10px; padding:0 4px; }}
QTextEdit        {{ background:{BG2}; border:1px solid #3a3a3a;
                    border-radius:4px; color:{FG}; padding:4px; }}
QPushButton      {{ background:{BTN}; color:{FG}; border:1px solid #3a3a3a;
                    border-radius:4px; padding:5px 14px; }}
QPushButton:hover {{ border-color:{ACC}; background:#333321; }}
QCheckBox        {{ spacing:8px; }}
QCheckBox::indicator {{ width:15px; height:15px; border-radius:3px;
                        border:1px solid #555; background:{BG2}; }}
QCheckBox::indicator:checked {{ background:{ACC}; border-color:{ACC}; }}
QSlider::groove:horizontal {{ height:4px; background:#3a3a3a; border-radius:2px; }}
QSlider::handle:horizontal {{ background:{ACC}; width:14px; height:14px;
                               margin:-5px 0; border-radius:7px; }}
QScrollArea {{ border:none; }}
QSpinBox {{ background:{BG2}; border:1px solid #3a3a3a; color:{FG};
            border-radius:4px; padding:2px 6px; }}
"""

ACCENT_BTN = f"""
QPushButton {{ background:{ACC}; color:#111; font-weight:bold;
               border:none; border-radius:4px; padding:6px 22px; }}
QPushButton:hover {{ background:#e8c540; }}
"""

CATEGORIES = [
    ("typo",         "Typo detected (4+ backspaces)"),
    ("idle",         "Idle / bored"),
    ("scroll",       "Scroll reaction"),
    ("click_near",   "Clicked near stickman"),
    ("fullscreen",   "Fullscreen / game opened"),
    ("drag_drop",    "Being dragged"),
    ("notif",        "Notification spotted"),
    ("hackerman",    "Fast typing streak"),
    ("window_move",  "Window moved"),
    ("cpu_sweat",    "CPU warning (60–79%)"),
    ("cpu_hamster",  "CPU critical (80%+) — hamster wheel"),
    ("ram_panic",    "RAM critical (80%+)"),
    ("cleanup_done", "Cleanup finished  ({count}, {size})"),
    ("drop",         "Dropped after drag"),
]


class SettingsWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, stick=None, parent=None):
        super().__init__(parent)
        self._stick = stick
        self.setWindowTitle("Stickman — Settings")
        self.setMinimumSize(580, 640)
        self.setStyleSheet(QSS)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        
        bar = QFrame()
        bar.setFixedHeight(46)
        bar.setStyleSheet(f"background:{BG2}; border-bottom:1px solid #2e2e2e;")
        bl  = QHBoxLayout(bar); bl.setContentsMargins(18, 0, 18, 0)
        lbl = QLabel("STICKMAN  SETTINGS")
        lbl.setFont(QFont("Consolas", 12, QFont.Bold))
        lbl.setStyleSheet(f"color:{ACC};")
        bl.addWidget(lbl)
        root.addWidget(bar)

       
        self._tabs = QTabWidget()
        self._tabs.addTab(self._tab_texts(),    "Texts")
        self._tabs.addTab(self._tab_behavior(), "Behavior")
        self._tabs.addTab(self._tab_actions(),  "Actions")
        self._tabs.addTab(self._tab_about(),    "About")
        root.addWidget(self._tabs)

        
        foot = QFrame()
        foot.setFixedHeight(52)
        foot.setStyleSheet(f"background:{BG2}; border-top:1px solid #2e2e2e;")
        fl = QHBoxLayout(foot); fl.setContentsMargins(18, 0, 18, 0)
        fl.addStretch()
        b_reset = QPushButton("Reset all")
        b_reset.clicked.connect(self._reset_all)
        b_save  = QPushButton("Save & Close")
        b_save.setStyleSheet(ACCENT_BTN)
        b_save.clicked.connect(self._save)
        fl.addWidget(b_reset); fl.addWidget(b_save)
        root.addWidget(foot)

        self._edits = {}

    
    def _tab_texts(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setSpacing(10); lay.setContentsMargins(12,12,12,12)

        info = QLabel("One message per line. Variables: {count}, {size}")
        info.setStyleSheet(f"color:{FG2}; font-size:11px;")
        lay.addWidget(info)

        for key, label in CATEGORIES:
            grp = QGroupBox(label); gl = QVBoxLayout(grp)
            te  = QTextEdit()
            te.setFixedHeight(86)
            te.setPlainText("\n".join(cfg.texts(key)))
            self._edits[key] = te
            gl.addWidget(te)
            row = QHBoxLayout(); row.addStretch()
            btn = QPushButton("Reset"); btn.setFixedWidth(80)
            btn.clicked.connect(lambda _, k=key: self._reset_cat(k))
            row.addWidget(btn); gl.addLayout(row)
            lay.addWidget(grp)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    
    def _tab_behavior(self):
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(18,18,18,18); lay.setSpacing(14)

        self._chk = {}
        for key, label in [
            ("notifications",   "React to notifications"),
            ("fullscreen_rage", "Rage-quit on fullscreen games"),
            ("drag_enabled",    "Draggable with mouse"),
            ("bubble_enabled",  "Show speech bubbles"),
            ("cpu_reactions",   "CPU reactions (sweat / hamster wheel)"),
            ("ram_reactions",   "RAM reactions (panic)"),
            ("cleanup_enabled", "Enable cleanup animation"),
        ]:
            c = QCheckBox(label); c.setChecked(cfg.get(key, True))
            c.stateChanged.connect(lambda v, k=key: cfg.set(k, bool(v)))
            self._chk[key] = c; lay.addWidget(c)

        
        grp = QGroupBox("Thresholds"); gl = QVBoxLayout(grp)
        for key, label, lo, hi in [
            ("cpu_warn_pct",   "CPU sweat starts (%)", 10, 95),
            ("cpu_hamster_pct","CPU hamster starts (%)", 10, 99),
            ("ram_warn_pct",   "RAM panic starts (%)", 20, 99),
            ("idle_warn_sec",  "Idle comment (sec)", 5, 120),
            ("idle_sleep_sec", "Idle sleep (sec)", 10, 300),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            sp  = QSpinBox(); sp.setRange(lo, hi)
            sp.setValue(cfg.get(key, 60))
            sp.valueChanged.connect(lambda v, k=key: cfg.set(k, v))
            row.addWidget(sp)
            gl.addLayout(row)
        lay.addWidget(grp)
        lay.addStretch()
        return w

    
    def _tab_actions(self):
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(18,18,18,18); lay.setSpacing(12)
        lay.addWidget(QLabel("Manual triggers (also in tray menu):"))

        for label, fn in [
            ("Make him dance",           lambda: self._stick and self._stick.trigger_dance()),
            ("Scare him",                lambda: self._stick and self._stick.trigger_scare()),
            ("Simulate notification",    lambda: self._stick and self._stick.trigger_notif()),
            ("Start cleanup animation",  lambda: self._stick and self._stick.trigger_cleanup()),
        ]:
            btn = QPushButton(label); btn.clicked.connect(fn)
            lay.addWidget(btn)

        lay.addStretch()
        return w

    
    def _tab_about(self):
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(24,24,24,24); lay.setSpacing(8)
        t = QLabel("Stickman Desktop Pet  v4.0")
        t.setFont(QFont("Consolas", 14, QFont.Bold))
        t.setStyleSheet(f"color:{ACC};")
        lay.addWidget(t)
        for line in [
            "", "A golden stickman that lives on your desktop.",
            "He sits on your windows, reacts to your typing,",
            "watches your CPU, panics about your RAM, and",
            "rides a garbage truck to clean your temp files.",
            "", "Drag him anywhere. Right-click tray for quick actions.",
        ]:
            l = QLabel(line); l.setStyleSheet(f"color:{FG2};")
            lay.addWidget(l)
        lay.addStretch()
        return w

    
    def _save(self):
        for k, te in self._edits.items():
            lines = [l.strip() for l in te.toPlainText().splitlines() if l.strip()]
            cfg.set_texts(k, lines or ["..."])
        cfg.save(); self.close()

    def _reset_cat(self, k):
        cfg.reset_texts(k)
        if k in self._edits:
            self._edits[k].setPlainText("\n".join(cfg.texts(k)))

    def _reset_all(self):
        if QMessageBox.question(self, "Reset", "Reset everything to defaults?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            cfg.reset_all(); self.close()

    def closeEvent(self, e):
        self.closed.emit(); super().closeEvent(e)
