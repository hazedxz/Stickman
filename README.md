# 🟡 Stickman Desktop Pet versión Beta

Interactive desktop mascot inspired by the style of the video, made 100% with Python and PyQt5.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Behaviors

| Situation | Stickman reaction |
|----------|---------------------
| You write normal | TYPING mode — arms in hackerman mode |
| You give 4+ backspaces in a row | LAUGHs at you + bubble with friendly insult |
| You write in an intense burst (20+ hot keys) | Dance + "HACKERMAN 🔥" |
| You don't do anything for 15 sec | Sarcastic bubble ("skill issue", "bored.exe"...) |
| You don't do anything for 30 sec | You FALL ASLEEP with floating ZZZs |
| Mouse scroll | Jump and scream |
| Mouse near stickman | You scare him, he runs away |
| You move the mouse | LOOKS at you with the visor hand |
| Window changes | Fall, walk/run to the new edge |
| Window far away | Run (faster animation) |
| Tray menu → "Make you dance" | Dance with musical notes |
| Tray menu → "Scare" | Panic + random push |

## Facial expressions
----this was removed.

- 😐 Normal — eyes and simple smile
- 😂 Laughing — half-closed eyes, big smile, crying emoji
- 😱 Scared — big eyes, open mouth
- 😴 Sleeping — eyes closed, ZZZs
- 👀 Looking at mouse — pupils following the cursor
- 😛 Typing — concentration language

## Technical extras

- Multi-monitor resolution detection (SM_CXVIRTUALSCREEN)
- Real physics: gravity, friction, pushing
- Fade-out text bubble
- 60 FPS smooth with antialiasing
- Tray icon with action menu
- Notification upon startup

## Add more reactions (easy)

In `_on_key_press`, add conditions:
```python
if key == keyboard.Key.f5:
    self._special_state(DANCING_STATE)
    self._say("Deploy")
```
