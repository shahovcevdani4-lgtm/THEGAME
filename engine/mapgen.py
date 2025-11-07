# engine/mapgen.py
import random
from data.tiles import TILES

def generate_map(width: int, height: int):
    """Создаёт случайную карту с лесками и камнями."""
    game_map = [[TILES["grass"] for _ in range(width)] for _ in range(height)]

    # генерация очагов леса
    num_forests = random.randint(3, 6)
    for _ in range(num_forests):
        fx = random.randint(0, width - 1)
        fy = random.randint(0, height - 1)
        radius = random.randint(2, 5)

        for y in range(max(0, fy - radius), min(height, fy + radius + 1)):
            for x in range(max(0, fx - radius), min(width, fx + radius + 1)):
                dist = ((x - fx) ** 2 + (y - fy) ** 2) ** 0.5
                if dist < radius and random.random() < 0.7:
                    game_map[y][x] = TILES["tree"]

    # редкие камни
    for _ in range(random.randint(15, 25)):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        game_map[y][x] = TILES["stone"]

    return game_map
