"""Non-hostile world characters with their own inventories and stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from engine.inventory import Inventory

@dataclass
class Character:
    """A friendly or neutral unit that inhabits the world."""

    name: str
    char: str
    fg: Tuple[int, int, int]
    bg: Tuple[int, int, int]
    stats: dict
    x: int
    y: int
    screen_x: int
    screen_y: int
    inventory: Inventory = field(default_factory=Inventory)
    tile_key: str | None = None

    @property
    def strength(self) -> int:
        return self.stats.get("str", 0)

    @property
    def agility(self) -> int:
        return self.stats.get("agi", 0)

    @property
    def intelligence(self) -> int:
        return self.stats.get("int", 0)

    def average_power(self) -> float:
        return (self.strength + self.agility + self.intelligence) / 3
