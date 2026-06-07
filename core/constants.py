# core/constants.py
from PyQt5.QtGui import QColor

# ── Stickman visuals ─────────────────────────────────────────
STICK_COLOR  = QColor(210, 175, 55)
STICK_W      = 4          # thin lines for elegant stickman
HEAD_R       = 10         # small head
TORSO_LEN    = 38         # tall torso
LEG_LEN      = 24
ARM_LEN      = 19

# ── Physics ──────────────────────────────────────────────────
GRAVITY       = 0.90
FRICTION      = 0.78
WALK_SPD      = 3.6
RUN_SPD       = 8.5
RUN_THRESH    = 200       # px before switching to run
JUMP_F        = -15.0
BOUNCE_D      = 0.30      # bounce damping on land

# ── Timing ───────────────────────────────────────────────────
TYPING_GRACE  = 0.36      # seconds of key silence before "stopped typing"
SP_COOLDOWN   = 0.9       # min seconds between special states
IDLE_WARN     = 20
IDLE_SLEEP    = 45
CPU_CHECK_INT = 3.0       # seconds between cpu/ram reads

# ── States ───────────────────────────────────────────────────
ST_FALLING   = 0
ST_WALKING   = 1
ST_SITTING   = 2
ST_TYPING    = 3
ST_DANCING   = 4
ST_LAUGHING  = 5
ST_SCARED    = 6
ST_SLEEPING  = 7
ST_RUNNING   = 8
ST_DRAGGED   = 9
ST_RAGEQUIT  = 10
ST_NOTIF     = 11
ST_SWEATING  = 12   # cpu 60-79%
ST_HAMSTER   = 13   # cpu 80%+
ST_RAM_PANIC = 14   # ram 80%+
ST_CLEANUP   = 15   # riding garbage truck
ST_LANDING   = 16   # squash on land

# ── Default text pools ───────────────────────────────────────
DEFAULT_TEXTS = {
    "typo":         ["bro😭", "really?", "skill issue", "ctrl+z exists",
                     "404: fingers not found", "try again", "gg", "touch grass"],
    "idle":         ["...", "hello?", "still there?", "bored.exe",
                     "u alive?", "tap something", "wake up", "*crickets*"],
    "scroll":       ["WHEEE", "whoa!", "watch it", "too fast!"],
    "click_near":   ["hey!", "oof", "watch it", "personal space!"],
    "fullscreen":   ["really? a game?", "ok fine, leaving",
                     "i hate you", "unbelievable"],
    "drag_drop":    ["put me down!", "seriously?", "rude.", "hey!!"],
    "notif":        ["u got mail", "hey, notification!", "go check that"],
    "hackerman":    ["HACKERMAN", "h4ck the planet", "u type fast ngl"],
    "window_move":  ["WOAH", "whoa!", "earthquake?!", "bro..."],
    "cpu_sweat":    ["sweating...", "it's hot in here",
                     "ur cpu bro💀", "this machine is suffering"],
    "cpu_hamster":  ["ur cpu bro💀", "what are u running??",
                     "pls stop", "i can't anymore"],
    "ram_panic":    ["ram full bro💀", "close something",
                     "how many tabs??", "ur pc is crying"],
    "cleanup_done": ["took out the trash", "done! freed {size}",
                     "cleaned {count} files", "ur pc can breathe now"],
    "drop":         ["ow", "thud.", "finally", "..rude"],
}
