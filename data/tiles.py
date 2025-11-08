"""Definitions for tiles and biome-specific palettes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from data.loader import load_game_data


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


def _colour_tuple(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return tuple(int(component) for component in value)
    return tuple(value)


def _normalise_tile(tile: Mapping[str, object]) -> dict[str, object]:
    normalised = dict(tile)
    for key in ("fg", "bg"):
        if key in normalised:
            normalised[key] = _colour_tuple(normalised[key])
    return normalised


def _normalise_tileset(raw_tiles: Mapping[str, Mapping[str, object]]) -> dict[str, dict]:
    return {str(name): _normalise_tile(data) for name, data in raw_tiles.items()}


def _range_tuple(value) -> tuple[int, int]:
    if isinstance(value, (list, tuple)):
        values = list(value)
    else:
        return (0, 0)
    if not values:
        return (0, 0)
    if len(values) == 1:
        values = [values[0], values[0]]
    return int(values[0]), int(values[1])


def _normalise_biomes(raw_biomes: Mapping[str, Mapping[str, object]]) -> dict[str, dict]:
    biomes: dict[str, dict] = {}
    for name, config in raw_biomes.items():
        normalised: dict[str, object] = dict(config)
        normalised["unique_tiles"] = _normalise_tileset(
            normalised.get("unique_tiles", {})  # type: ignore[arg-type]
        )
        overrides = normalised.get("overrides")
        if isinstance(overrides, Mapping):
            normalised["overrides"] = _normalise_tileset(overrides)
        extras = normalised.get("extras")
        if isinstance(extras, Mapping):
            normalised["extras"] = _normalise_tileset(extras)
        forest_tiles = normalised.get("forest_tiles", ())
        if isinstance(forest_tiles, (list, tuple)):
            normalised["forest_tiles"] = tuple(str(tile) for tile in forest_tiles)
        else:
            normalised["forest_tiles"] = ()
        normalised["forest_count"] = _range_tuple(normalised.get("forest_count", (3, 6)))
        normalised["forest_radius"] = _range_tuple(normalised.get("forest_radius", (2, 5)))
        forest_density = normalised.get("forest_density", 0.7)
        try:
            normalised["forest_density"] = float(forest_density)
        except (TypeError, ValueError):
            normalised["forest_density"] = 0.7
        rules = []
        raw_rules = normalised.get("scatter_rules", [])
        if isinstance(raw_rules, (list, tuple)):
            for rule in raw_rules:
                if isinstance(rule, Mapping):
                    tile = str(rule.get("tile", ""))
                    count_range = _range_tuple(rule.get("count_range", (0, 0)))
                    avoid_border = bool(rule.get("avoid_border", True))
                    rules.append(
                        ScatterRule(
                            tile=tile,
                            count_range=count_range,
                            avoid_border=avoid_border,
                        )
                    )
        normalised["scatter_rules"] = tuple(rules)
        biomes[str(name)] = normalised
    return biomes


def _load_tiles_data() -> tuple[dict[str, dict], dict[str, dict]]:
    data = load_game_data().get("tiles", {})
    common_tiles = _normalise_tileset(data.get("common_tiles", {}))
    biomes = _normalise_biomes(data.get("biomes", {}))
    return common_tiles, biomes


COMMON_TILES, BIOME_CONFIGS = _load_tiles_data()


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
            override_tile = overrides[name]
            override = dict(override_tile)
            for key in ("fg", "bg"):
                if key in override and override[key] is not None:
                    override[key] = _colour_tuple(override[key])
            tile.update(override)
        tiles[name] = tile

    for name, data in extras.items():
        tile = data.copy()
        tile.setdefault("ground_tile", ground_key)
        tiles[name] = tile

    return tiles, ground_key


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
        config = BIOME_CONFIGS.get(biome, BIOME_CONFIGS.get("summer", {}))
        _BIOME_CACHE[biome] = _build_biome(biome, config)
    return _BIOME_CACHE[biome]


def get_biome_tiles(biome: str) -> dict[str, dict]:
    """Compatibility helper returning only the tile palette for a biome."""

    return get_biome_definition(biome).tiles


# Default tile set used for player initialization and ASCII fallback.
TILES = get_biome_tiles("summer")
