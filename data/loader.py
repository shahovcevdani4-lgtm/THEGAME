"""Utility helpers to load and persist structured game data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_DATA_FILE = Path(__file__).with_name("game_data.json")


def load_game_data() -> dict[str, Any]:
    """Load the shared data file that powers the editor and the game."""

    if not _DATA_FILE.exists():
        raise FileNotFoundError(
            "Не найден файл данных игры. Ожидался data/game_data.json."
        )
    with _DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_game_data(data: Mapping[str, Any]) -> None:
    """Persist the shared data file with pretty-printed JSON."""

    with _DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
