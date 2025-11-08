"""Inventory model and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Inventory:
    columns: int = 3
    rows: int = 3
    slots: list[Any | None] = field(default_factory=lambda: [None] * 9)
    cursor_index: int = 0

    def __post_init__(self) -> None:
        total = self.columns * self.rows
        if len(self.slots) != total:
            self.slots = list(self.slots)[:total]
            self.slots.extend([None] * (total - len(self.slots)))

    def move_cursor(self, dx: int, dy: int) -> None:
        """Move the selection cursor within the inventory grid."""

        if dx == 0 and dy == 0:
            return
        x, y = self.cursor_position
        new_x = min(max(0, x + dx), self.columns - 1)
        new_y = min(max(0, y + dy), self.rows - 1)
        self.cursor_index = new_y * self.columns + new_x

    @property
    def cursor_position(self) -> tuple[int, int]:
        row, col = divmod(self.cursor_index, self.columns)
        return col, row

    def slot_at(self, index: int) -> Any | None:
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def selected_item(self) -> Any | None:
        return self.slot_at(self.cursor_index)
