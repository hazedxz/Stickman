# core/renderer.py  — pure drawing, zero state logic
import math, random
from PyQt5.QtCore  import Qt, QPoint, QRect, QPointF
from PyQt5.QtGui   import (QPainter, QPen, QBrush, QColor,
                            QFont, QPolygon, QRadialGradient,
                            QLinearGradient, QPainterPath)
from core.constants import (STICK_COLOR, STICK_W, HEAD_R, TORSO_LEN, LEG_LEN, ARM_LEN,
                             ST_FALLING, ST_WALKING, ST_SITTING, ST_TYPING,
                             ST_DANCING, ST_LAUGHING, ST_SCARED, ST_SLEEPING,
                             ST_RUNNING, ST_DRAGGED, ST_RAGEQUIT, ST_NOTIF,
                             ST_SWEATING, ST_HAMSTER, ST_RAM_PANIC,
                             ST_CLEANUP, ST_LANDING)

# Palette
_C_LAPTOP_BASE  = QColor(220, 220, 220)
_C_LAPTOP_SCR   = QColor(60,  170, 255)
_C_LAPTOP_LOGO  = QColor(250, 250, 250)
_C_CHAIR        = QColor(140,  95,  40)
_C_PILLOW       = QColor(100, 140, 210)
_C_SWEAT        = QColor(80,  160, 255, 200)
_C_WHEEL        = QColor(80,   80,  80)
_C_WHEEL_BAR    = QColor(110, 110, 110)
_C_TRUCK_BODY   = QColor(50,  160,  60)
_C_TRUCK_CABIN  = QColor(40,  130,  50)
_C_TRUCK_WHEEL  = QColor(30,   30,  30)
_C_TRASH_BAG    = QColor(40,   40,  40)
_C_RAM_BLOCK    = QColor(180, 60,  60)

TL = TORSO_LEN
LL = LEG_LEN
AL = ARM_LEN
HR = HEAD_R


# ─────────────────────────────────────────────────────────────
def draw_frame(painter: QPainter, cx: int, cy: int,
               state: int, direction: int, t: float,
               bubble_text: str, bubble_elapsed: float, bubble_dur: float,
               zzz_off: float, drag_wobble: float,
               cleanup_pct: float):
    """
    cx, cy  = foot-centre of stickman (bottom of torso)
    t       = time.time() * 10
    cleanup_pct = 0..1 progress of cleanup animation
    """
    painter.setRenderHint(QPainter.Antialiasing)

    # ── Bobbing / breath when idle ───────────────────────────
    bob = math.sin(t / 2.6) * 1.6 if state in (ST_SITTING, ST_NOTIF) else 0.0

    # ── Landing squash ───────────────────────────────────────
    squash = 1.0
    if state == ST_LANDING:
        squash = 0.78 + 0.22 * abs(math.sin(t * 3))

    # ── Drag wobble ──────────────────────────────────────────
    wob = math.sin(t * 3.5) * drag_wobble

    # ── Special full-body animations (no stickman base) ──────
    if state == ST_HAMSTER:
        _draw_hamster_scene(painter, cx, cy, t)
        if bubble_text:
            _draw_bubble(painter, cx, int(cy - HR*2 - 10), bubble_text, bubble_elapsed, bubble_dur)
        return

    if state == ST_CLEANUP:
        _draw_garbage_truck(painter, cx, cy, t, cleanup_pct)
        if bubble_text:
            _draw_bubble(painter, cx, int(cy - HR*2 - 10), bubble_text, bubble_elapsed, bubble_dur)
        return

    if state == ST_RAM_PANIC:
        _draw_ram_panic(painter, cx, cy, t, direction)
        if bubble_text:
            _draw_bubble(painter, cx, int(cy - HR*2 - 10), bubble_text, bubble_elapsed, bubble_dur)
        return

    # ── Props behind stickman ────────────────────────────────
    if state in (ST_SITTING, ST_TYPING):
        _draw_chair(painter, cx, cy, direction)
    if state == ST_SLEEPING:
        _draw_pillow(painter, cx, cy, direction)

    # ── Head ─────────────────────────────────────────────────
    hx = cx + int(wob)
    hy = int(cy - HR * 2 - bob)
    _set_pen(painter)
    painter.drawEllipse(hx - HR, hy, HR * 2, HR * 2)

    # ── Torso ─────────────────────────────────────────────────
    lean = 5 * direction if state in (ST_WALKING, ST_RUNNING) else 0
    lean = int(lean + wob * 0.5)
    tx = cx + lean
    ty = int(cy + TL * squash)
    painter.drawLine(hx, int(cy - bob), tx, ty)

    # ── Limbs ─────────────────────────────────────────────────
    _draw_limbs(painter, hx, cy, tx, ty, state, direction, t, bob, wob, squash)

    # ── Laptop (in front) ────────────────────────────────────
    if state in (ST_SITTING, ST_TYPING):
        _draw_laptop(painter, cx, cy, direction, t, state)

    # ── Sweat drops when CPU 60-79% ──────────────────────────
    if state == ST_SWEATING:
        _draw_sweat(painter, hx, hy, t)

    # ── Particle FX ──────────────────────────────────────────
    _draw_effects(painter, cx, cy, state, t, zzz_off)

    # ── Bubble ───────────────────────────────────────────────
    if bubble_text:
        _draw_bubble(painter, hx, hy, bubble_text, bubble_elapsed, bubble_dur)


# ═════════════════════════════════════════════════════════════
#  LIMBS
# ═════════════════════════════════════════════════════════════
def _draw_limbs(p, cx, cy, tx, ty, state, d, t, bob, wob, squash):
    _set_pen(p)

    if state == ST_FALLING:
        # Starfish panic — arms and legs spread wide, wiggling
        flail = math.sin(t * 2.0) * 7
        p.drawLine(cx, int(cy-bob), int(cx-AL-4), int(cy-AL+flail))
        p.drawLine(cx, int(cy-bob), int(cx+AL+4), int(cy-AL-flail))
        p.drawLine(tx, ty, int(tx-LL-4), int(ty+LL+flail))
        p.drawLine(tx, ty, int(tx+LL+4), int(ty+LL-flail))

    elif state in (ST_WALKING, ST_RUNNING):
        spd  = 1.9 if state == ST_RUNNING else 1.05
        mag  = 1.5 if state == ST_RUNNING else 1.0
        op   = math.sin(t * spd) * LL * mag
        ob   = math.cos(t * spd) * AL * mag
        # Legs — two-segment for realism
        knee_l = int(tx - op * 0.5)
        knee_r = int(tx + op * 0.5)
        knee_y = int(ty + LL * 0.55)
        p.drawLine(tx, ty, knee_l, knee_y)
        p.drawLine(knee_l, knee_y, int(tx - op), int(ty + LL))
        p.drawLine(tx, ty, knee_r, knee_y)
        p.drawLine(knee_r, knee_y, int(tx + op), int(ty + LL))
        # Arms swing opposite
        p.drawLine(cx, int(cy-bob), int(cx - ob), int(cy + 14))
        p.drawLine(cx, int(cy-bob), int(cx + ob), int(cy + 14))

    elif state in (ST_SITTING, ST_TYPING, ST_SWEATING):
        # Seated: thigh horizontal, shin down (two-segment legs)
        thigh_end_x = int(tx + 20 * d)
        p.drawLine(tx, ty, thigh_end_x, ty)
        p.drawLine(thigh_end_x, ty, thigh_end_x, int(ty + LL))
        if state == ST_TYPING:
            c1 = random.randint(-8, 8)
            c2 = random.randint(-8, 8)
            p.drawLine(cx, int(cy-bob), int(cx+AL*d),   int(cy+10+c1))
            p.drawLine(cx, int(cy-bob), int(cx+AL*d+4), int(cy+5+c2))
        else:
            p.drawLine(cx, int(cy-bob), int(cx+8*d),  int(cy+16))
            p.drawLine(cx, int(cy-bob), int(cx-5*d),  int(cy+16))

    elif state == ST_DANCING:
        # Fluid wave through whole body
        w1 = math.sin(t * 2.4) * 22
        w2 = math.cos(t * 2.4) * 18
        w3 = math.sin(t * 2.4 + 1) * 18
        p.drawLine(cx, int(cy-bob), int(cx+w1), int(cy-14))
        p.drawLine(cx, int(cy-bob), int(cx-w1), int(cy+10))
        # Legs bounce
        lk_y = int(ty + LL * 0.5)
        p.drawLine(tx, ty, int(tx+w2*0.6), lk_y)
        p.drawLine(int(tx+w2*0.6), lk_y, int(tx+w2), int(ty+LL))
        p.drawLine(tx, ty, int(tx-w3*0.6), lk_y)
        p.drawLine(int(tx-w3*0.6), lk_y, int(tx-w3), int(ty+LL))

    elif state == ST_LAUGHING:
        # Bent over laughing, slapping knee
        osc = math.sin(t * 5.0) * 10
        p.drawLine(cx, int(cy-bob), int(cx-AL-2), int(cy+osc+8))
        p.drawLine(cx, int(cy-bob), int(cx+AL+2), int(cy-osc+8))
        p.drawLine(tx, ty, int(tx-LL*0.7), int(ty+LL*0.9))
        p.drawLine(tx, ty, int(tx+LL*0.7), int(ty+LL*0.9))

    elif state == ST_SCARED:
        # Arms straight up trembling
        tr = math.sin(t * 8) * 5
        p.drawLine(cx, int(cy-bob), int(cx-AL-2+tr), int(cy-AL-8))
        p.drawLine(cx, int(cy-bob), int(cx+AL+2-tr), int(cy-AL-8))
        p.drawLine(tx, ty, int(tx-LL*0.6+tr), int(ty+LL))
        p.drawLine(tx, ty, int(tx+LL*0.6-tr), int(ty+LL))

    elif state == ST_SLEEPING:
        # Limp arms/legs, slumped
        p.drawLine(cx, int(cy-bob), int(cx-14), int(cy+22))
        p.drawLine(cx, int(cy-bob), int(cx+6),  int(cy+20))
        p.drawLine(tx, ty, int(tx-LL*0.8), int(ty+LL*0.85))
        p.drawLine(tx, ty, int(tx+5),      int(ty+LL*0.6))

    elif state == ST_DRAGGED:
        # Ragdoll — dangly limbs
        dang = math.sin(t * 5.5) * 14
        p.drawLine(cx, int(cy-bob), int(cx-AL+dang), int(cy+10))
        p.drawLine(cx, int(cy-bob), int(cx+AL-dang), int(cy+10))
        p.drawLine(tx, ty, int(tx-LL*0.7+dang), int(ty+LL))
        p.drawLine(tx, ty, int(tx+LL*0.7-dang), int(ty+LL))

    elif state == ST_RAGEQUIT:
        # Throwing tantrum — stomping
        stomp = math.sin(t * 7) * 16
        p.drawLine(cx, int(cy-bob), int(cx-AL-4), int(cy-AL+stomp))
        p.drawLine(cx, int(cy-bob), int(cx+AL+4), int(cy-AL-stomp))
        lk_y = int(ty + LL * 0.5)
        p.drawLine(tx, ty, int(tx-10), lk_y)
        p.drawLine(int(tx-10), lk_y, int(tx-LL*0.8), int(ty+LL))
        p.drawLine(tx, ty, int(tx+10), lk_y)
        p.drawLine(int(tx+10), lk_y, int(tx+LL*0.8), int(ty+LL))

    elif state == ST_NOTIF:
        # Excited run toward notif
        spd = 2.0
        op  = math.sin(t * spd) * LL * 1.3
        ob  = math.cos(t * spd) * AL * 1.2
        lk_y = int(ty + LL * 0.55)
        p.drawLine(tx, ty, int(tx-op*0.5), lk_y)
        p.drawLine(int(tx-op*0.5), lk_y, int(tx-op), int(ty+LL))
        p.drawLine(tx, ty, int(tx+op*0.5), lk_y)
        p.drawLine(int(tx+op*0.5), lk_y, int(tx+op), int(ty+LL))
        p.drawLine(cx, int(cy-bob), int(cx-ob), int(cy+12))
        p.drawLine(cx, int(cy-bob), int(cx+ob), int(cy+12))

    elif state == ST_LANDING:
        # Squashed — legs wide, arms out for balance
        p.drawLine(tx, ty, int(tx-LL),  int(ty+8))
        p.drawLine(tx, ty, int(tx+LL),  int(ty+8))
        p.drawLine(cx, int(cy-bob), int(cx-AL-4), int(cy+4))
        p.drawLine(cx, int(cy-bob), int(cx+AL+4), int(cy+4))


# ═════════════════════════════════════════════════════════════
#  PROPS
# ═════════════════════════════════════════════════════════════
def _draw_chair(p, cx, cy, d):
    p.setPen(QPen(_C_CHAIR, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    sy = cy + TL + 3
    p.drawLine(cx-22, sy, cx+22, sy)                      # seat
    p.drawLine(cx-16, sy, cx-16, sy+22)                   # leg L
    p.drawLine(cx+16, sy, cx+16, sy+22)                   # leg R
    p.drawLine(cx-22*d, sy, cx-22*d, sy-24)               # back post
    p.drawLine(cx-22*d, sy-24, cx-8*d, sy-24)             # back rail
    _set_pen(p)

def _draw_pillow(p, cx, cy, d):
    px = cx + 20*d; py = cy + TL + 6
    p.setPen(QPen(_C_PILLOW.darker(120), 2))
    p.setBrush(QBrush(_C_PILLOW))
    p.drawRoundedRect(px-18, py-10, 36, 20, 10, 10)
    _set_pen(p)

def _draw_laptop(p, cx, cy, d, t, state):
    base_y = cy + TL - 1
    bx     = cx + 15*d
    wobble = math.sin(t * 0.7) * 1.2 if state == ST_TYPING else 0

    # Keyboard base
    p.setPen(QPen(_C_LAPTOP_BASE.darker(110), 2))
    p.setBrush(QBrush(_C_LAPTOP_BASE))
    p.drawRoundedRect(bx-15, base_y, 30, 7, 2, 2)

    # Screen
    scr_h = 22
    scr_x = bx - 14
    scr_y = int(base_y - scr_h + wobble)
    p.drawRoundedRect(scr_x, scr_y, 28, scr_h, 2, 2)

    # Screen glow
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(_C_LAPTOP_SCR))
    p.drawRoundedRect(scr_x+2, scr_y+2, 24, scr_h-4, 1, 1)

    # Apple logo
    p.setBrush(QBrush(_C_LAPTOP_LOGO))
    p.setPen(QPen(_C_LAPTOP_LOGO, 1))
    p.drawEllipse(scr_x+9, scr_y+7, 9, 9)

    _set_pen(p)


# ═════════════════════════════════════════════════════════════
#  HAMSTER WHEEL SCENE
# ═════════════════════════════════════════════════════════════
def _draw_hamster_scene(p, cx, cy, t):
    """Full replacement scene: stickman running inside a hamster wheel."""
    WR = 48   # wheel radius

    # Wheel shadow
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(0,0,0,40)))
    p.drawEllipse(cx-WR+4, cy-WR*2+4, WR*2, WR*2)

    # Wheel rim
    p.setPen(QPen(_C_WHEEL, 5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(QBrush(QColor(60,60,60,60)))
    p.drawEllipse(cx-WR, cy-WR*2, WR*2, WR*2)

    # Spokes (rotating)
    spoke_angle = (t * 4.5) % (2 * math.pi)
    for i in range(6):
        a = spoke_angle + i * math.pi / 3
        sx = int(cx + WR*0.85 * math.cos(a))
        sy = int((cy - WR) + WR*0.85 * math.sin(a))
        p.setPen(QPen(_C_WHEEL_BAR, 3))
        p.drawLine(cx, cy-WR, sx, sy)

    # Hub
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(_C_WHEEL))
    p.drawEllipse(cx-6, cy-WR-6, 12, 12)

    # Stand
    p.setPen(QPen(_C_WHEEL, 5))
    p.drawLine(cx-WR, cy, cx-WR-10, cy+20)
    p.drawLine(cx+WR, cy, cx+WR+10, cy+20)

    # Stickman running inside wheel
    run_phase = t * 4.5
    op = math.sin(run_phase) * 18
    ob = math.cos(run_phase) * 14
    wy = cy - WR    # center of wheel

    _set_pen(p)
    # Head
    p.drawEllipse(cx-HR, wy-HR*2-TL, HR*2, HR*2)
    # Torso
    p.drawLine(cx, wy-TL, cx+4, wy)
    # Legs (two-segment)
    lk = int(wy + LL*0.5)
    p.drawLine(cx+4, wy, int(cx+4-op*0.5), lk)
    p.drawLine(int(cx+4-op*0.5), lk, int(cx+4-op), int(wy+LL))
    p.drawLine(cx+4, wy, int(cx+4+op*0.5), lk)
    p.drawLine(int(cx+4+op*0.5), lk, int(cx+4+op), int(wy+LL))
    # Arms
    p.drawLine(cx, wy-TL, int(cx-ob), int(wy-TL+14))
    p.drawLine(cx, wy-TL, int(cx+ob), int(wy-TL+14))

    # Sweat flying off
    sw_t = t * 3
    for i in range(3):
        a = math.pi / 4 + i * math.pi / 6
        dist = 28 + (sw_t * 6 + i * 20) % 30
        sx = int(cx + math.cos(a) * dist)
        sy = int((wy-TL) + math.sin(a) * dist * 0.5)
        alpha = max(0, int(230 - (sw_t * 6 + i*20) % 30 * 7))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(80, 160, 255, alpha)))
        p.drawEllipse(sx-3, sy-4, 5, 8)
        _set_pen(p)


# ═════════════════════════════════════════════════════════════
#  GARBAGE TRUCK SCENE
# ═════════════════════════════════════════════════════════════
def _draw_garbage_truck(p, cx, cy, t, pct):
    """Stickman riding a garbage truck, bags flying in."""
    # Truck body — drives from right to center
    tx_off = int((1.0 - min(pct * 2, 1.0)) * 300) if pct < 0.5 else 0
    bx     = cx + tx_off

    # Shadow
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(0,0,0,35)))
    p.drawEllipse(bx-55, cy+20, 110, 14)

    # Truck body
    p.setPen(QPen(_C_TRUCK_BODY.darker(120), 2))
    p.setBrush(QBrush(_C_TRUCK_BODY))
    p.drawRoundedRect(bx-60, cy-25, 100, 50, 5, 5)

    # Cabin
    p.setBrush(QBrush(_C_TRUCK_CABIN))
    p.drawRoundedRect(bx+20, cy-40, 45, 55, 5, 5)

    # Windshield
    p.setBrush(QBrush(QColor(120,200,255,180)))
    p.setPen(QPen(Qt.white, 1))
    p.drawRoundedRect(bx+24, cy-36, 35, 28, 3, 3)

    # Wheels (rotating)
    wrot = t * 3.5
    for wx_off in [-35, 40]:
        wx = bx + wx_off; wy = cy + 26
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(_C_TRUCK_WHEEL))
        p.drawEllipse(wx-14, wy-14, 28, 28)
        p.setBrush(QBrush(QColor(100,100,100)))
        p.drawEllipse(wx-5, wy-5, 10, 10)
        # Tread lines
        p.setPen(QPen(QColor(60,60,60), 2))
        for i in range(4):
            a = wrot + i * math.pi/2
            p.drawLine(wx, wy,
                       int(wx + 12*math.cos(a)), int(wy + 12*math.sin(a)))

    # Compactor door (animated open/close)
    door_open = abs(math.sin(t * 1.5))
    p.setPen(QPen(_C_TRUCK_BODY.darker(150), 2))
    p.setBrush(QBrush(_C_TRUCK_BODY.darker(130)))
    p.drawRect(bx-60, cy-25, int(20 + door_open*8), 50)

    # Trash bags flying into truck (during pct 0..0.6)
    if pct < 0.7:
        for i in range(4):
            bag_phase = (t * 2.5 + i * 1.57) % (2 * math.pi)
            bpx = int(bx - 60 - 80 + (pct * 180 + i * 30) % 100)
            bpy = int(cy - 10 - abs(math.sin(bag_phase)) * 60)
            alpha = min(255, int(pct * 400))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(40,40,40,alpha)))
            p.drawEllipse(bpx-10, bpy-12, 20, 24)
            # Bag tie
            p.setPen(QPen(QColor(100,100,100,alpha), 2))
            p.drawLine(bpx-5, bpy-12, bpx+5, bpy-12)

    # Stickman sitting on top of truck, waving
    sx = bx - 20; sy = cy - 30
    wave = math.sin(t * 3) * 18

    _set_pen(p)
    # Head
    p.drawEllipse(sx-HR, sy-HR*2-TL, HR*2, HR*2)
    # Torso
    p.drawLine(sx, sy-TL, sx, sy)
    # Legs dangling
    p.drawLine(sx, sy, sx-14, sy+LL)
    p.drawLine(sx, sy, sx+8, sy+LL-5)
    # One arm waving, one holding on
    p.drawLine(sx, sy-TL, int(sx+AL), int(sy-TL+8))   # hold
    p.drawLine(sx, sy-TL, int(sx-AL*0.6), int(sy-TL-wave*0.5))  # wave

    # Done label
    if pct > 0.85:
        _draw_count_badge(p, bx, cy-55, pct)

    _set_pen(p)


def _draw_count_badge(p, cx, cy, pct):
    alpha = int(min(1.0, (pct - 0.85) / 0.15) * 220)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(30,180,60,alpha)))
    p.drawRoundedRect(cx-30, cy-12, 60, 24, 8, 8)
    p.setPen(QPen(QColor(255,255,255,alpha)))
    p.setFont(QFont("Consolas", 9, QFont.Bold))
    p.drawText(QRect(cx-30, cy-12, 60, 24), Qt.AlignCenter, "DONE!")


# ═════════════════════════════════════════════════════════════
#  RAM PANIC SCENE
# ═════════════════════════════════════════════════════════════
def _draw_ram_panic(p, cx, cy, t, direction):
    """Stickman surrounded by RAM blocks crushing in."""
    squish = abs(math.sin(t * 1.2)) * 0.3

    # RAM blocks closing in from sides
    for i, side in enumerate([-1, 1]):
        dist = 80 - squish * 40
        bx = int(cx + side * dist)
        p.setPen(QPen(_C_RAM_BLOCK.darker(120), 2))
        p.setBrush(QBrush(_C_RAM_BLOCK))
        p.drawRoundedRect(bx - 28, cy - 40, 28, 75, 4, 4)
        # Memory chip detail
        p.setPen(QPen(QColor(255,180,180), 1))
        for row in range(4):
            p.drawRect(bx-24, cy-30+row*14, 20, 8)

    # Floor RAM block rising
    rise = int(squish * 30)
    p.setPen(QPen(_C_RAM_BLOCK.darker(140), 2))
    p.setBrush(QBrush(_C_RAM_BLOCK.darker(110)))
    p.drawRoundedRect(cx-45, cy+TL+rise, 90, 20, 4, 4)

    # Panicking stickman in middle (compressed vertically)
    sy_scale = 1.0 - squish * 0.4
    _set_pen(p)
    # Head
    p.drawEllipse(cx-HR, int(cy - HR*2*(sy_scale)), HR*2, HR*2)
    # Torso (shorter)
    torso_end = int(cy + TL * sy_scale)
    p.drawLine(cx, cy, cx, torso_end)
    # Arms waving frantically
    flail = math.sin(t * 7) * 14
    p.drawLine(cx, cy, int(cx-AL-flail), int(cy-8))
    p.drawLine(cx, cy, int(cx+AL+flail), int(cy-8))
    # Legs squished
    p.drawLine(cx, torso_end, int(cx-LL*0.6), int(torso_end+LL*sy_scale))
    p.drawLine(cx, torso_end, int(cx+LL*0.6), int(torso_end+LL*sy_scale))

    # Sweat drops
    _draw_sweat(p, cx, int(cy-HR*2), t)


# ═════════════════════════════════════════════════════════════
#  SWEAT DROPS
# ═════════════════════════════════════════════════════════════
def _draw_sweat(p, hx, hy, t):
    """Animated sweat drops off the head."""
    p.setPen(Qt.NoPen)
    for i in range(3):
        phase = (t * 2.5 + i * 2.1) % 6.28
        sx    = int(hx + math.cos(phase) * (HR + 4 + i * 3))
        fall  = (t * 15 + i * 30) % 40
        sy    = int(hy + fall)
        alpha = max(0, int(230 - fall * 5))
        p.setBrush(QBrush(QColor(80, 160, 255, alpha)))
        p.drawEllipse(sx-3, sy, 5, 8)
    _set_pen(p)


# ═════════════════════════════════════════════════════════════
#  PARTICLE EFFECTS
# ═════════════════════════════════════════════════════════════
def _draw_effects(p, cx, cy, state, t, zzz_off):
    if state == ST_SLEEPING:
        fnt = QFont("Arial", 11, QFont.Bold)
        p.setFont(fnt)
        for i, letter in enumerate(["z","Z","Z"]):
            ox = int(i*14 + zzz_off*0.26)
            oy = int(-HR*3.5 - i*16 - zzz_off)
            a  = max(0, 210 - i*55)
            p.setPen(QPen(QColor(140,200,255,a)))
            p.drawText(cx+ox, cy+oy, letter)

    elif state == ST_DANCING:
        fnt = QFont("Arial", 13)
        p.setFont(fnt)
        notes = ["♪","♫","♩","♬"]
        for i, n in enumerate(notes):
            ox  = int(math.sin(t+i*1.8)*30)
            oy  = int(-HR*3.2 - i*16 - (t*3.5+i*5)%55)
            a   = max(0, int(240 - (t*3.5+i*5)%55*4))
            p.setPen(QPen(QColor(255,220,55,a)))
            p.drawText(cx+ox, cy+oy, n)

    elif state == ST_LAUGHING:
        fnt = QFont("Segoe UI Emoji", 12)
        p.setFont(fnt)
        p.setPen(QPen(QColor(255,200,50,220)))
        p.drawText(cx-8, cy-int(HR*3.8), "😭")

    elif state == ST_RAGEQUIT:
        fnt = QFont("Arial", 10, QFont.Bold)
        p.setFont(fnt)
        syms = ["!","!!","#@$","!!!","@#$!"]
        for i, s in enumerate(syms):
            ox  = int(math.sin(t*2.2+i)*24)
            oy  = int(-HR*2.8 - i*13 - (t*4.5+i*3)%42)
            a   = max(0, int(240-(t*4.5+i*3)%42*5))
            p.setPen(QPen(QColor(255,70,40,a)))
            p.drawText(cx+ox, cy+oy, s)

    _set_pen(p)


# ═════════════════════════════════════════════════════════════
#  SPEECH BUBBLE
# ═════════════════════════════════════════════════════════════
def _draw_bubble(p, hx, hy, text, elapsed, duration):
    if not text or elapsed >= duration:
        return
    fade = duration * 0.65
    alpha = 255
    if elapsed > fade:
        alpha = max(0, int(255 * (1.0-(elapsed-fade)/(duration-fade))))

    fnt = QFont("Consolas", 9, QFont.Bold)
    p.setFont(fnt)
    fm  = p.fontMetrics()
    tw  = fm.horizontalAdvance(text)
    th  = fm.height()
    pad = 8
    bw  = tw + pad*2
    bh  = th + pad*2
    bx  = hx - bw//2
    by  = hy - bh - 14

    # Shadow
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(0,0,0, min(alpha//3, 80))))
    p.drawRoundedRect(bx+2, by+2, bw, bh, 7, 7)

    # BG
    p.setBrush(QBrush(QColor(15,15,15,alpha)))
    p.setPen(QPen(QColor(210,175,55,alpha), 1))
    p.drawRoundedRect(bx, by, bw, bh, 7, 7)

    # Tail
    tail = QPolygon([QPoint(hx-5,by+bh), QPoint(hx+5,by+bh), QPoint(hx,by+bh+10)])
    p.setBrush(QBrush(QColor(15,15,15,alpha)))
    p.setPen(QPen(QColor(210,175,55,alpha), 1))
    p.drawPolygon(tail)

    # Text
    p.setPen(QPen(QColor(255,248,200,alpha)))
    p.drawText(bx+pad, by+pad+th-3, text)
    _set_pen(p)


# ═════════════════════════════════════════════════════════════
#  HELPER
# ═════════════════════════════════════════════════════════════
def _set_pen(p):
    p.setPen(QPen(STICK_COLOR, STICK_W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QBrush(STICK_COLOR))
