# engine/player.py
import random

from data.tiles import TILES


class Player:
    def __init__(
        self,
        x: int,
        y: int,
        stats: dict,
        *,
        tile=None,
        screen_x: int = 0,
        screen_y: int = 0,
    ):
        self.x = x
        self.y = y
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.tile = tile or TILES["player"].copy()
        self.stats = stats
        self.max_hp = 20 + stats.get("str", 0) * 2
        self.hp = self.max_hp
        self.talents = 100
        self._footprints: dict[tuple[int, int], list[tuple[int, int]]] = {}

    @property
    def strength(self) -> int:
        return self.stats.get("str", 0)

    @property
    def dexterity(self) -> int:
        return self.stats.get("dex", 0)

    @property
    def intelligence(self) -> int:
        return self.stats.get("int", 0)

    def average_power(self) -> float:
        return (self.strength + self.dexterity + self.intelligence) / 3

    def attack_damage(self) -> int:
        return random.randint(1, max(1, self.strength))

    def position(self) -> tuple[int, int, int, int]:
        return self.screen_x, self.screen_y, self.x, self.y

    def set_position(
        self, screen_x: int, screen_y: int, x: int, y: int
    ) -> None:
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.x = x
        self.y = y

    def leave_footprint(
        self, screen_coords: tuple[int, int], position: tuple[int, int], limit: int = 2
    ) -> None:
        footprints = self._footprints.setdefault(screen_coords, [])
        if position in footprints:
            footprints.remove(position)
        footprints.append(position)
        if len(footprints) > limit:
            del footprints[0 : len(footprints) - limit]

    def get_footprints(self, screen_coords: tuple[int, int]) -> list[tuple[int, int]]:
        return list(self._footprints.get(screen_coords, []))

    def clear_footprints(self, screen_coords: tuple[int, int]) -> None:
        self._footprints.pop(screen_coords, None)
