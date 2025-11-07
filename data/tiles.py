# data/tiles.py
import tcod

# базовые цвета
DARK_GREEN = tcod.Color(0, 60, 0)
GRASS_GREEN = tcod.Color(0, 120, 0)
TREE_GREEN = tcod.Color(100, 200, 100)
STONE_GRAY = tcod.Color(130, 130, 130)
PLAYER_GOLD = tcod.Color(240, 200, 80)

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
