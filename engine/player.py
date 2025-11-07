# engine/player.py
import random

from data.tiles import TILES

class Player:
    def __init__(self, x: int, y: int, stats: dict, tile=None):
        self.x = x
        self.y = y
        self.tile = tile or TILES["player"]
        self.stats = stats
        self.max_hp = 20 + stats.get("str", 0) * 2
        self.hp = self.max_hp
        self.talents = 100

    @property
    def strength(self) -> int:
        return self.stats.get("str", 0)

    @property
    def dexterity(self) -> int:
        return self.stats.get("dex", 0)

    @property
    def intelligence(self) -> int:
        return self.stats.get("int", 0)

    def move(self, dx: int, dy: int, game_map) -> bool:
        """Двигает игрока, если клетка проходима."""
        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_y < len(game_map) and 0 <= new_x < len(game_map[0]):
            target = game_map[new_y][new_x]
            if target["walkable"]:
                self.x = new_x
                self.y = new_y
                return True
        return False

    def average_power(self) -> float:
        return (self.strength + self.dexterity + self.intelligence) / 3

    def attack_damage(self) -> int:
        return random.randint(1, max(1, self.strength))
