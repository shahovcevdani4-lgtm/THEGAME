"""Definitions for tiles and biome-specific palettes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ScatterRule:
    """Rule describing how to scatter additional objects on a biome map."""

    tile: str
    count_range: tuple[int, int]
    avoid_border: bool = True


@dataclass(frozen=True)
class BiomeDefinition:
    """Complete description of a biome tileset and spawning behaviour."""

    name: str
    tiles: dict[str, dict]
    ground_tile: str
    forest_tiles: Sequence[str]
    forest_count: tuple[int, int]
    forest_radius: tuple[int, int]
    forest_density: float
    scatter_rules: Sequence[ScatterRule]


# Base colours shared between tiles.  The renderer will fall back to these
# values whenever a sprite image is missing, so they double as ASCII colours.
PLAYER_GOLD = (240, 200, 80)
ENEMY_RED = (120, 0, 40)
WARLOCK_PURPLE = (180, 0, 200)
WARLOCK_BG = (20, 0, 40)

SUMMER_GRASS_FG = (20, 150, 40)
SUMMER_GRASS_BG = (5, 70, 15)
SUMMER_TREE_FG = (90, 200, 90)
SUMMER_TREE_BG = SUMMER_GRASS_BG
SUMMER_ROCK_FG = (130, 130, 130)

WINTER_SNOW_FG = (230, 230, 255)
WINTER_SNOW_BG = (210, 210, 235)
WINTER_TREE_FG = (30, 90, 160)
WINTER_TREE_BG = WINTER_SNOW_BG
WINTER_SNOWDRIFT_FG = (200, 200, 230)

DROUGHT_SAND_FG = (215, 180, 90)
DROUGHT_SAND_BG = (170, 130, 60)
DROUGHT_CACTUS_FG = (60, 140, 70)
DROUGHT_WOOD_FG = (150, 90, 40)


COMMON_TILES: Mapping[str, dict] = {
    "player": {
        "char": "@",
        "fg": PLAYER_GOLD,
        "bg": None,
        "walkable": True,
        "tile_id": "player",
    },
    "enemy": {
        "char": "E",
        "fg": (255, 230, 230),
        "bg": ENEMY_RED,
        "walkable": False,
        "tile_id": "enemy",
    },
    "warlock": {
        "char": "§",
        "fg": WARLOCK_PURPLE,
        "bg": WARLOCK_BG,
        "walkable": False,
        "tile_id": "warlock",
    },
}


def _build_tileset(config: Mapping[str, object]) -> tuple[dict[str, dict], str]:
    """Construct the final tile dictionary for a biome configuration."""

    ground_key = config["ground_tile"]  # type: ignore[index]
    unique_tiles: Mapping[str, dict] = config["unique_tiles"]  # type: ignore[index]
    overrides: Mapping[str, Mapping[str, object]] = config.get(  # type: ignore[assignment]
        "overrides", {}
    )
    extras: Mapping[str, dict] = config.get("extras", {})  # type: ignore[assignment]

    tiles: dict[str, dict] = {}

    for name, data in unique_tiles.items():
        tile = data.copy()
        tile.setdefault("ground_tile", ground_key)
        tiles[name] = tile

    ground_bg = tiles[ground_key]["bg"]

    for name, base in COMMON_TILES.items():
        tile = base.copy()
        tile.setdefault("ground_tile", ground_key)
        if tile.get("bg") is None:
            tile["bg"] = ground_bg
        if name in overrides:
            tile.update(overrides[name])
        tiles[name] = tile

    for name, data in extras.items():
        tile = data.copy()
        tile.setdefault("ground_tile", ground_key)
        tiles[name] = tile

    return tiles, ground_key


BIOME_CONFIGS: Mapping[str, dict] = {
    "summer": {
        "ground_tile": "summer_ground",
        "unique_tiles": {
            "summer_ground": {
                "char": ".",
                "fg": SUMMER_GRASS_FG,
                "bg": SUMMER_GRASS_BG,
                "walkable": True,
                "tile_id": "summer_ground",
            },
            "summer_tree": {
                "char": "♣",
                "fg": SUMMER_TREE_FG,
                "bg": SUMMER_TREE_BG,
                "walkable": False,
                "tile_id": "summer_tree",
            },
            "summer_boulder": {
                "char": "▲",
                "fg": SUMMER_ROCK_FG,
                "bg": SUMMER_GRASS_BG,
                "walkable": False,
                "tile_id": "summer_boulder",
            },
        },
        "forest_tiles": ("summer_tree",),
        "forest_count": (3, 6),
        "forest_radius": (2, 5),
        "forest_density": 0.7,
        "scatter_rules": (ScatterRule("summer_boulder", (12, 22)),),
    },
    "winter": {
        "ground_tile": "winter_ground",
        "unique_tiles": {
            "winter_ground": {
                "char": "·",
                "fg": WINTER_SNOW_FG,
                "bg": WINTER_SNOW_BG,
                "walkable": True,
                "tile_id": "winter_ground",
            },
            "winter_tree": {
                "char": "Y",
                "fg": WINTER_TREE_FG,
                "bg": WINTER_TREE_BG,
                "walkable": False,
                "tile_id": "winter_tree",
            },
            "winter_snowdrift": {
                "char": "~",
                "fg": WINTER_SNOWDRIFT_FG,
                "bg": WINTER_SNOW_BG,
                "walkable": True,
                "tile_id": "winter_snowdrift",
            },
        },
        "forest_tiles": ("winter_tree",),
        "forest_count": (3, 6),
        "forest_radius": (2, 5),
        "forest_density": 0.7,
        "scatter_rules": (
            ScatterRule("winter_snowdrift", (18, 28), avoid_border=False),
        ),
        "extras": {
            "footprint": {
                "char": "'",
                "fg": WINTER_SNOWDRIFT_FG,
                "bg": WINTER_SNOW_BG,
                "walkable": True,
                "tile_id": "footprint",
            }
        },
    },
    "drought": {
        "ground_tile": "drought_ground",
        "unique_tiles": {
            "drought_ground": {
                "char": "`",
                "fg": DROUGHT_SAND_FG,
                "bg": DROUGHT_SAND_BG,
                "walkable": True,
                "tile_id": "drought_ground",
            },
            "drought_cactus": {
                "char": "†",
                "fg": DROUGHT_CACTUS_FG,
                "bg": DROUGHT_SAND_BG,
                "walkable": False,
                "tile_id": "drought_cactus",
            },
            "drought_dead_tree": {
                "char": "T",
                "fg": DROUGHT_WOOD_FG,
                "bg": DROUGHT_SAND_BG,
                "walkable": False,
                "tile_id": "drought_dead_tree",
            },
        },
        "forest_tiles": ("drought_cactus", "drought_dead_tree"),
        "forest_count": (3, 6),
        "forest_radius": (2, 5),
        "forest_density": 0.6,
        "scatter_rules": (
            ScatterRule("drought_cactus", (8, 14)),
            ScatterRule("drought_dead_tree", (6, 12)),
        ),
    },
}


def _build_biome(name: str, config: Mapping[str, object]) -> BiomeDefinition:
    tiles, ground_key = _build_tileset(config)
    return BiomeDefinition(
        name=name,
        tiles=tiles,
        ground_tile=ground_key,
        forest_tiles=config.get("forest_tiles", ()),
        forest_count=config.get("forest_count", (3, 6)),
        forest_radius=config.get("forest_radius", (2, 5)),
        forest_density=config.get("forest_density", 0.7),
        scatter_rules=config.get("scatter_rules", ()),
    )


_BIOME_CACHE: dict[str, BiomeDefinition] = {}


def get_biome_definition(biome: str) -> BiomeDefinition:
    """Return the biome definition with cached construction."""

    if biome not in _BIOME_CACHE:
        config = BIOME_CONFIGS.get(biome, BIOME_CONFIGS["summer"])
        _BIOME_CACHE[biome] = _build_biome(biome, config)
    return _BIOME_CACHE[biome]


def get_biome_tiles(biome: str) -> dict[str, dict]:
    """Compatibility helper returning only the tile palette for a biome."""

    return get_biome_definition(biome).tiles


# Default tile set used for player initialization and ASCII fallback.
TILES = get_biome_tiles("summer")

