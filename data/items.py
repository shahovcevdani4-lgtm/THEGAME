"""Definitions for equippable items that the editor can manage."""
from __future__ import annotations

from typing import Dict

from data.loader import load_game_data


def _normalise_item(entry: dict) -> dict:
    normalised = dict(entry)
    normalised["name"] = str(normalised.get("name", ""))
    normalised["icon"] = str(normalised.get("icon", ""))
    normalised["slot_type"] = str(normalised.get("slot_type", ""))
    normalised["two_handed"] = bool(normalised.get("two_handed", False))
    if "tile" in normalised and normalised["tile"]:
        normalised["tile"] = str(normalised["tile"])
    if "damage_bonus" in normalised:
        try:
            normalised["damage_bonus"] = int(normalised["damage_bonus"])
        except (TypeError, ValueError):
            normalised.pop("damage_bonus", None)
    return normalised


def _load_items() -> Dict[str, dict]:
    data = load_game_data()
    items = data.get("items", {})
    return {name: _normalise_item(values) for name, values in items.items()}


ITEMS = _load_items()
