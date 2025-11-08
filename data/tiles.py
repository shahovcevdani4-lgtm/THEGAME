# data/tiles.py

# базовые цвета (RGB-кортежи подходят tcod так же, как и tcod.Color)
DARK_GREEN = (0, 60, 0)
GRASS_GREEN = (0, 120, 0)
TREE_GREEN = (100, 200, 100)
STONE_GRAY = (130, 130, 130)
PLAYER_GOLD = (240, 200, 80)

SNOW_WHITE = (230, 230, 255)
WINTER_TREE_BLUE = (30, 60, 120)
WINTER_STONE_GRAY = (170, 170, 180)

SAND_YELLOW = (180, 150, 70)
DROUGHT_TREE_BROWN = (140, 90, 40)


BASE_TILES = {
    "grass": {
        "char": ".",  # базовый фон
        "fg": GRASS_GREEN,
        "bg": DARK_GREEN,
        "walkable": True,
        "tile_id": "grass",
    },
    "tree": {
        "char": "/",  # дерево
        "fg": TREE_GREEN,
        "bg": DARK_GREEN,
        "walkable": False,
        "tile_id": "tree",
    },
    "stone": {
        "char": "o",  # камень
        "fg": STONE_GRAY,
        "bg": DARK_GREEN,
        "walkable": False,
        "tile_id": "stone",
    },
    "player": {
        "char": "@",
        "fg": PLAYER_GOLD,
        "bg": DARK_GREEN,
        "walkable": True,
        "tile_id": "player",
    },
}


BIOME_OVERRIDES = {
    "summer": {
        "grass": {"fg": GRASS_GREEN, "bg": DARK_GREEN},
        "tree": {"fg": TREE_GREEN, "bg": DARK_GREEN},
        "stone": {"fg": STONE_GRAY, "bg": DARK_GREEN},
    },
    "winter": {
        "grass": {"fg": SNOW_WHITE, "bg": SNOW_WHITE},
        "tree": {"fg": WINTER_TREE_BLUE, "bg": SNOW_WHITE},
        "stone": {"fg": WINTER_STONE_GRAY, "bg": SNOW_WHITE},
        "player": {"bg": SNOW_WHITE},
        "_extra": {
            "footprint": {
                "char": "'",
                "fg": (200, 200, 230),
                "bg": SNOW_WHITE,
                "walkable": True,
                "tile_id": "footprint",
            }
        },
    },
    "drought": {
        "grass": {"fg": SAND_YELLOW, "bg": SAND_YELLOW},
        "tree": {"fg": DROUGHT_TREE_BROWN, "bg": SAND_YELLOW},
        "stone": {"fg": STONE_GRAY, "bg": SAND_YELLOW},
        "player": {"bg": SAND_YELLOW},
    },
}


def get_biome_tiles(biome: str):
    """Собрать тайлы для указанного биома."""

    overrides = BIOME_OVERRIDES.get(biome, BIOME_OVERRIDES["summer"])
    tiles = {}
    for name, base in BASE_TILES.items():
        tile = base.copy()
        if name in overrides:
            tile.update(overrides[name])
        tiles[name] = tile

    for extra_name, data in overrides.get("_extra", {}).items():
        tiles[extra_name] = data.copy()

    return tiles


# совместимость со старыми импортами
TILES = get_biome_tiles("summer")
