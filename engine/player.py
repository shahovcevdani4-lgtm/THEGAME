# engine/player.py
import random

from data.tiles import TILES
from engine.constants import AGILITY_SPEED_BONUS, BASE_MOVEMENT_SPEED
from engine.inventory import Inventory, InventoryItem


class Player:
    def __init__(
        self,
        x: int,
        y: int,
        stats: dict,
        *,
        name: str = "Игрок",
        character_class: str = "",
        tile=None,
        screen_x: int = 0,
        screen_y: int = 0,
    ):
        self.x = x
        self.y = y
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.tile = tile or TILES["player"].copy()
        self.tile_key = self.tile.get("tile_id", "player")
        self.name = name
        self.character_class = character_class
        self.stats = stats
        self.max_hp = 20 + stats.get("str", 0) * 2
        self.hp = self.max_hp
        self.talents = 100
        self._footprints: dict[tuple[int, int], list[tuple[int, int]]] = {}
        self.inventory = Inventory()
        self._seed_starting_items()
        self.facing = 1

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

    def attack_damage(self) -> int:
        return random.randint(1, max(1, self.strength))

    @property
    def movement_speed(self) -> float:
        """Возвращает скорость передвижения в клетках в секунду."""

        return BASE_MOVEMENT_SPEED + self.agility * AGILITY_SPEED_BONUS

    @property
    def movement_interval(self) -> float:
        """Минимальное время между шагами в секундах."""

        speed = self.movement_speed
        if speed <= 0:
            return 0.0
        return 1.0 / speed

    def position(self) -> tuple[int, int, int, int]:
        return self.screen_x, self.screen_y, self.x, self.y

    def set_position(
        self, screen_x: int, screen_y: int, x: int, y: int
    ) -> None:
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.x = x
        self.y = y

    def update_facing(self, dx: int) -> None:
        if dx < 0:
            self.facing = 1
        elif dx > 0:
            self.facing = -1

    def leave_footprint(
        self,
        screen_coords: tuple[int, int],
        position: tuple[int, int],
        limit: int | None = None,
    ) -> None:
        footprints = self._footprints.setdefault(screen_coords, [])
        if position in footprints:
            footprints.remove(position)
        footprints.append(position)
        if limit is not None and len(footprints) > limit:
            del footprints[0 : len(footprints) - limit]

    def get_footprints(self, screen_coords: tuple[int, int]) -> list[tuple[int, int]]:
        return list(self._footprints.get(screen_coords, []))

    def clear_footprints(self, screen_coords: tuple[int, int]) -> None:
        self._footprints.pop(screen_coords, None)

    def _seed_starting_items(self) -> None:
        """Populate the backpack with a few basic items for testing equipment."""

        starters = [
            InventoryItem("Тёплый плащ", "C", "upper"),
            InventoryItem("Походные сапоги", "B", "boots"),
            InventoryItem("Кинжал", "/", "weapon", damage_bonus=2),
            InventoryItem("Алебарда", "†", "weapon", two_handed=True, damage_bonus=4),
        ]

        for index, item in enumerate(starters):
            if index < len(self.inventory.passive_slots):
                self.inventory.passive_slots[index] = item
