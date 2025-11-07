# data/tiles.py

# базовые цвета (RGB-кортежи подходят tcod так же, как и tcod.Color)
DARK_GREEN = (0, 60, 0)
GRASS_GREEN = (0, 120, 0)
TREE_GREEN = (100, 200, 100)
STONE_GRAY = (130, 130, 130)
PLAYER_GOLD = (240, 200, 80)

# словарь тайлов
TILES = {
    "grass": {
        "char": ".",                # трава — базовый фон
        "fg": GRASS_GREEN,
        "bg": DARK_GREEN,
        "walkable": True,
    },
    "tree": {
        "char": "/",                # дерево
        "fg": TREE_GREEN,
        "bg": DARK_GREEN,
        "walkable": False,
    },
    "stone": {
        "char": "o",                # камень
        "fg": STONE_GRAY,
        "bg": DARK_GREEN,
        "walkable": False,
    },
    "player": {
        "char": "@",
        "fg": PLAYER_GOLD,
        "bg": DARK_GREEN,
        "walkable": True,
    },
}
