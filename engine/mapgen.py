"""Map generation routines that respect biome-specific object sets."""

from __future__ import annotations

import random
from typing import Sequence

from data.tiles import BiomeDefinition


def _pick_forest_tile(options: Sequence[str]) -> str | None:
    if not options:
        return None
    return random.choice(list(options))


def generate_map(width: int, height: int, biome: BiomeDefinition):
    """Create a random map using biome-specific tiles and scatter rules."""

    tiles = biome.tiles
    ground_key = biome.ground_tile
    ground_tile = tiles[ground_key]

    game_map = [[ground_tile.copy() for _ in range(width)] for _ in range(height)]

    min_forests, max_forests = biome.forest_count
    min_radius, max_radius = biome.forest_radius
    density = biome.forest_density

    num_forests = random.randint(min_forests, max_forests)
    for _ in range(num_forests):
        fx = random.randint(1, width - 2)
        fy = random.randint(1, height - 2)
        radius = random.randint(min_radius, max_radius)

        for y in range(max(0, fy - radius), min(height, fy + radius + 1)):
            for x in range(max(0, fx - radius), min(width, fx + radius + 1)):
                if x in (0, width - 1) or y in (0, height - 1):
                    continue
                dist = ((x - fx) ** 2 + (y - fy) ** 2) ** 0.5
                if dist < radius and random.random() < density:
                    tile_name = _pick_forest_tile(biome.forest_tiles)
                    if tile_name:
                        game_map[y][x] = tiles[tile_name].copy()

    for rule in biome.scatter_rules:
        count = random.randint(*rule.count_range)
        tile_name = rule.tile
        if tile_name not in tiles:
            continue
        for _ in range(count):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if rule.avoid_border and (x in (0, width - 1) or y in (0, height - 1)):
                continue
            game_map[y][x] = tiles[tile_name].copy()

    return game_map

