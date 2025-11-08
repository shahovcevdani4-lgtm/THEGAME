"""Definitions for hostile creatures encountered on the map."""
from __future__ import annotations

from typing import Dict

from data.loader import load_game_data


def _normalise_enemy(entry: dict) -> dict:
    normalised = dict(entry)
    for key in ("fg", "bg"):
        if key in normalised and normalised[key] is not None:
            normalised[key] = tuple(normalised[key])
    if "stats" in normalised and isinstance(normalised["stats"], dict):
        normalised["stats"] = dict(normalised["stats"])
    return normalised


def _load_enemies() -> Dict[str, dict]:
    data = load_game_data()
    enemies = data.get("enemies", {})
    return {name: _normalise_enemy(values) for name, values in enemies.items()}


ENEMIES = _load_enemies()
