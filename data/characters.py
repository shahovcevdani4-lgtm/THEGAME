"""Definitions of non-hostile characters encountered in the world."""
from __future__ import annotations

from typing import Dict

from data.loader import load_game_data


def _normalise_colors(entry: dict) -> dict:
    normalised = dict(entry)
    for key in ("fg", "bg"):
        if key in normalised and normalised[key] is not None:
            normalised[key] = tuple(normalised[key])
    if "stats" in normalised and isinstance(normalised["stats"], dict):
        normalised["stats"] = dict(normalised["stats"])
    return normalised


def _load_characters() -> Dict[str, dict]:
    data = load_game_data()
    characters = data.get("characters", {})
    return {name: _normalise_colors(values) for name, values in characters.items()}


CHARACTERS = _load_characters()
