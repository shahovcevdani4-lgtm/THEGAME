# engine/player.py
from data.tiles import TILES

class Player:
    def __init__(self, x: int, y: int, tile=None):
        self.x = x
        self.y = y
        self.tile = tile or TILES["player"]

    def move(self, dx: int, dy: int, game_map):
        """Двигает игрока, если клетка проходима."""
        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_y < len(game_map) and 0 <= new_x < len(game_map[0]):
            target = game_map[new_y][new_x]
            if target["walkable"]:
                self.x = new_x
                self.y = new_y
