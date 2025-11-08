"""Data management helpers shared between the editor screens."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from data.loader import load_game_data, save_game_data


class GameDataManager:
    """Convenience wrapper around the shared JSON game data file."""

    def __init__(self) -> None:
        self.path = Path(__file__).resolve().parents[1] / "data" / "game_data.json"
        self.data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Reload data from disk."""

        self.data = load_game_data()

    def save(self) -> None:
        """Persist the current in-memory representation."""

        save_game_data(self.data)

    def section(self, name: str, default: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Return a mutable section from the game data."""

        if default is None:
            default = {}
        section = self.data.setdefault(name, dict(default))
        if not isinstance(section, dict):
            raise TypeError(f"Раздел {name!r} должен быть словарём")
        return section

    def replace_section(self, name: str, content: Mapping[str, Any]) -> None:
        """Replace a section with a new mapping."""

        self.data[name] = dict(content)

