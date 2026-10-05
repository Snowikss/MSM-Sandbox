from __future__ import annotations

import json
from pathlib import Path
from threading import RLock

from .models import PlayerState


DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "state.json"
_LOCK = RLock()


def load_state() -> PlayerState:
    with _LOCK:
        if not STATE_FILE.exists():
            state = PlayerState()
            save_state(state)
            return state

        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return PlayerState.model_validate(raw)


def save_state(state: PlayerState) -> None:
    with _LOCK:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(state.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
