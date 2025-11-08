"""Inventory model and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Iterable, List, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from engine.player import Player


_ACTIVE_SLOT_ORDER: Sequence[str] = (
    "upper",
    "boots",
    "weapon_main",
    "weapon_off",
)

_ACTIVE_SLOT_LABELS: dict[str, str] = {
    "upper": "Верхняя одежда",
    "boots": "Обувь",
    "weapon_main": "Правая рука",
    "weapon_off": "Левая рука",
}

_WEAPON_SLOTS: Sequence[str] = ("weapon_main", "weapon_off")


@dataclass
class InventoryItem:
    """Represents an item that can live in the player's inventory."""

    name: str
    icon: str
    slot_type: str
    two_handed: bool = False

    def symbol(self) -> str:
        """Return the preferred character for UI rendering."""

        if self.icon:
            return self.icon
        if self.name:
            return self.name[0].upper()
        return "*"


@dataclass
class Inventory:
    """Manages active equipment slots and passive backpack storage."""

    ACTIVE_SLOT_ORDER: ClassVar[Sequence[str]] = _ACTIVE_SLOT_ORDER
    ACTIVE_SLOT_LABELS: ClassVar[dict[str, str]] = _ACTIVE_SLOT_LABELS
    WEAPON_SLOTS: ClassVar[Sequence[str]] = _WEAPON_SLOTS

    passive_columns: int = 4
    passive_rows: int = 3
    passive_slots: List[InventoryItem | None] = field(default_factory=list)
    active_slots: dict[str, InventoryItem | None] = field(
        default_factory=lambda: {
            "upper": None,
            "boots": None,
            "weapon_main": None,
            "weapon_off": None,
        }
    )
    cursor_index: int = 0
    last_message: str = ""

    def __post_init__(self) -> None:
        total_passive = self.passive_columns * self.passive_rows
        if not self.passive_slots:
            self.passive_slots = [None] * total_passive
        elif len(self.passive_slots) != total_passive:
            slots = list(self.passive_slots)[:total_passive]
            slots.extend([None] * (total_passive - len(slots)))
            self.passive_slots = slots

        self.cursor_index = max(0, min(self.cursor_index, self.total_slots - 1))

    @property
    def columns(self) -> int:
        return self.passive_columns

    @property
    def rows(self) -> int:
        return 1 + self.passive_rows

    @property
    def total_slots(self) -> int:
        return len(self.ACTIVE_SLOT_ORDER) + self.passive_columns * self.passive_rows

    @property
    def cursor_position(self) -> tuple[int, int]:
        row, col = divmod(self.cursor_index, self.columns)
        return col, row

    def is_active_index(self, index: int) -> bool:
        return 0 <= index < len(self.ACTIVE_SLOT_ORDER)

    def selected_section(self) -> str:
        return "active" if self.is_active_index(self.cursor_index) else "passive"

    def slot_at(self, index: int) -> InventoryItem | None:
        if self.is_active_index(index):
            slot_name = self.ACTIVE_SLOT_ORDER[index]
            return self.active_slots.get(slot_name)
        passive_index = index - len(self.ACTIVE_SLOT_ORDER)
        if 0 <= passive_index < len(self.passive_slots):
            return self.passive_slots[passive_index]
        return None

    def slot_label(self, index: int) -> str:
        if self.is_active_index(index):
            slot_name = self.ACTIVE_SLOT_ORDER[index]
            return self.ACTIVE_SLOT_LABELS.get(slot_name, slot_name)
        passive_index = index - len(self.ACTIVE_SLOT_ORDER)
        return f"Рюкзак {passive_index + 1}"

    def selected_item(self) -> InventoryItem | None:
        return self.slot_at(self.cursor_index)

    def clear_message(self) -> None:
        self.last_message = ""

    @staticmethod
    def display_symbol(item) -> str:
        if item is None:
            return "·"
        symbol = getattr(item, "symbol", None)
        if callable(symbol):
            return symbol()
        if isinstance(item, str) and len(item) == 1:
            return item
        return str(item)[0]

    def active_slot_symbol(self, slot_name: str) -> str:
        return self.display_symbol(self.active_slots.get(slot_name))

    def passive_slot_symbol(self, index: int) -> str:
        return self.display_symbol(self.passive_slots[index])

    def is_two_handed_slot(self, slot_name: str) -> bool:
        item = self.active_slots.get(slot_name)
        if not item or not getattr(item, "two_handed", False):
            return False
        other = "weapon_off" if slot_name == "weapon_main" else "weapon_main"
        return self.active_slots.get(other) is item


    def move_cursor(self, dx: int, dy: int) -> None:
        """Move the selection cursor across active and passive slots."""

        if dx == 0 and dy == 0:
            return
        x, y = self.cursor_position
        new_x = max(0, min(self.columns - 1, x + dx))
        new_y = max(0, min(self.rows - 1, y + dy))
        self.cursor_index = min(self.total_slots - 1, new_y * self.columns + new_x)
        self.clear_message()

    def transfer_selected(self) -> bool:
        """Move the selected item between active and passive sections."""

        if self.selected_section() == "active":
            return self._transfer_active_to_passive()
        return self._transfer_passive_to_active()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _transfer_active_to_passive(self) -> bool:
        slot_name = self.ACTIVE_SLOT_ORDER[self.cursor_index]
        item = self.active_slots.get(slot_name)
        if item is None:
            self.last_message = "Слот пуст."
            return False
        if not self._has_free_passive_slot():
            self.last_message = "Нет свободного места в рюкзаке."
            return False

        if slot_name in self.WEAPON_SLOTS and item.two_handed:
            self._clear_weapon_item(item)
        else:
            self.active_slots[slot_name] = None

        self._store_in_passive(item)
        self.last_message = f"{item.name} перемещён в рюкзак."
        return True

    def _transfer_passive_to_active(self) -> bool:
        passive_index = self.cursor_index - len(self.ACTIVE_SLOT_ORDER)
        item = self.passive_slots[passive_index]
        if item is None:
            self.last_message = "Пустая ячейка."
            return False

        if item.slot_type == "upper":
            success = self._equip_to_single_slot("upper", item)
        elif item.slot_type == "boots":
            success = self._equip_to_single_slot("boots", item)
        elif item.slot_type == "weapon":
            success = self._equip_weapon(item)
        else:
            self.last_message = "Этот предмет нельзя активировать."
            return False

        if success:
            self.passive_slots[passive_index] = None
            target_section = "активные слоты" if item.slot_type != "weapon" else "оружие"
            self.last_message = f"{item.name} перемещён в {target_section}."
        return success

    def _equip_to_single_slot(self, slot_name: str, item: InventoryItem) -> bool:
        current = self.active_slots.get(slot_name)
        if current is item:
            self.last_message = "Предмет уже надет."
            return False
        if current is not None:
            if not self._has_free_passive_slot():
                self.last_message = "Нет места, чтобы снять текущий предмет."
                return False
            self.active_slots[slot_name] = None
            self._store_in_passive(current)

        self.active_slots[slot_name] = item
        return True

    def _equip_weapon(self, item: InventoryItem) -> bool:
        equipped_items = self._collect_weapon_items(exclude=item)
        free_slots = self._free_passive_slots()

        if item.two_handed:
            if len(equipped_items) > free_slots:
                self.last_message = "Нет места, чтобы освободить обе руки."
                return False
            for existing in equipped_items:
                self._clear_weapon_item(existing)
                self._store_in_passive(existing)
            self.active_slots["weapon_main"] = item
            self.active_slots["weapon_off"] = item
            return True

        # handle currently equipped two-handed weapons
        if any(existing.two_handed for existing in equipped_items):
            if len(equipped_items) > free_slots:
                self.last_message = "Нет места, чтобы освободить руки."
                return False
            for existing in equipped_items:
                self._clear_weapon_item(existing)
                self._store_in_passive(existing)
            equipped_items = []

        if any(self.active_slots[slot] is item for slot in self.WEAPON_SLOTS):
            self.last_message = "Предмет уже экипирован."
            return False

        for slot_name in self.WEAPON_SLOTS:
            if self.active_slots[slot_name] is None:
                self.active_slots[slot_name] = item
                return True

        if free_slots == 0:
            self.last_message = "Нет места, чтобы освободить руку."
            return False

        # move off-hand item to backpack by default
        off_item = self.active_slots["weapon_off"]
        if off_item is not None:
            self.active_slots["weapon_off"] = None
            self._store_in_passive(off_item)
            self.active_slots["weapon_off"] = item
            return True

        main_item = self.active_slots["weapon_main"]
        if main_item is not None:
            self.active_slots["weapon_main"] = None
            self._store_in_passive(main_item)
        self.active_slots["weapon_main"] = item
        return True

    def _store_in_passive(self, item: InventoryItem) -> int | None:
        for index, slot in enumerate(self.passive_slots):
            if slot is None:
                self.passive_slots[index] = item
                return index
        return None

    def _has_free_passive_slot(self) -> bool:
        return any(slot is None for slot in self.passive_slots)

    def _free_passive_slots(self) -> int:
        return sum(1 for slot in self.passive_slots if slot is None)

    def _collect_weapon_items(self, exclude: InventoryItem | None = None) -> List[InventoryItem]:
        collected: List[InventoryItem] = []
        for slot_name in self.WEAPON_SLOTS:
            item = self.active_slots.get(slot_name)
            if item is None:
                continue
            if exclude is not None and item is exclude:
                continue
            if item not in collected:
                collected.append(item)
        return collected

    def _clear_weapon_item(self, item: InventoryItem) -> None:
        for slot_name in self.WEAPON_SLOTS:
            if self.active_slots.get(slot_name) is item:
                self.active_slots[slot_name] = None

    def iter_active_slots(self) -> Iterable[tuple[str, InventoryItem | None]]:
        for slot_name in self.ACTIVE_SLOT_ORDER:
            yield slot_name, self.active_slots.get(slot_name)

    def passive_index_range(self) -> range:
        return range(len(self.ACTIVE_SLOT_ORDER), self.total_slots)


def build_inventory_context(player: "Player", talents_label: str) -> list[tuple[str, tuple[int, int, int]]]:
    inventory = player.inventory
    lines: list[tuple[str, tuple[int, int, int]]] = []

    lines.append((f"Имя: {player.name}", (245, 245, 245)))
    lines.append((f"Класс: {player.character_class}", (200, 200, 255)))
    stats_line = f"STR {player.strength}  AGI {player.agility}  INT {player.intelligence}"
    lines.append((stats_line, (200, 255, 200)))
    lines.append((talents_label, (255, 215, 0)))
    lines.append((f"Слот: {inventory.slot_label(inventory.cursor_index)}", (220, 220, 220)))

    selected = inventory.selected_item()
    if selected is not None:
        descriptor = selected.slot_type
        if descriptor == "upper":
            descriptor = "верхняя одежда"
        elif descriptor == "boots":
            descriptor = "обувь"
        elif descriptor == "weapon":
            descriptor = "оружие"
        item_line = f"Выбрано: {selected.name} ({descriptor})"
        if getattr(selected, "two_handed", False):
            item_line += " — двуручное"
        lines.append((item_line, (210, 230, 255)))
        description = getattr(selected, "description", "")
        if description:
            for chunk in str(description).split("\n"):
                if chunk.strip():
                    lines.append((chunk.strip(), (190, 200, 220)))

    if inventory.last_message:
        lines.append((inventory.last_message, (255, 230, 120)))

    lines.append(("Управление: WASD — выбор, E — перенос, I — закрыть", (180, 180, 200)))

    return lines
