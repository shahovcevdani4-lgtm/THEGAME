"""World-building helpers and data structures."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, TYPE_CHECKING

from data.characters import CHARACTERS
from data.enemies import ENEMIES
from data.tiles import BiomeDefinition, get_biome_definition
from engine.battle import Enemy
from engine.characters import Character
from engine.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_COLUMNS,
    WORLD_ROWS,
)
from engine.mapgen import generate_map

if TYPE_CHECKING:  # pragma: no cover - runtime import cycle guard
    from engine.player import Player


@dataclass
class WorldScreen:
    tiles: dict
    terrain: list[list[dict]]
    biome: str
    enemies: list[Enemy]
    characters: list[Character]


@dataclass
class World:
    screens: Dict[tuple[int, int], WorldScreen]
    spawn_screen: tuple[int, int]
    spawn_position: tuple[int, int]
    time_elapsed: float = 0.0

    def total_width(self) -> int:
        return MAP_WIDTH * WORLD_COLUMNS

    def total_height(self) -> int:
        return MAP_HEIGHT * WORLD_ROWS

    def get_screen(self, coords: tuple[int, int]) -> WorldScreen:
        return self.screens[coords]

    def map_at(self, coords: tuple[int, int]) -> list[list[dict]]:
        return self.get_screen(coords).terrain

    def tiles_at(self, coords: tuple[int, int]) -> dict:
        return self.get_screen(coords).tiles

    def biome_at(self, coords: tuple[int, int]) -> str:
        return self.get_screen(coords).biome

    def enemies_at(self, coords: tuple[int, int]) -> list[Enemy]:
        return self.get_screen(coords).enemies

    def characters_at(self, coords: tuple[int, int]) -> list[Character]:
        return self.get_screen(coords).characters

    def advance_time(self, delta: float) -> None:
        if delta <= 0:
            return
        self.time_elapsed += delta

    def _clamp_camera(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        max_x = max(0, self.total_width() - width)
        max_y = max(0, self.total_height() - height)
        return max(0, min(x, max_x)), max(0, min(y, max_y))

    def _screens_in_rect(
        self, start_x: int, start_y: int, width: int, height: int
    ) -> Iterator[tuple[int, int]]:
        if width <= 0 or height <= 0:
            return iter(())

        end_x = min(self.total_width(), start_x + width)
        end_y = min(self.total_height(), start_y + height)
        left = start_x // MAP_WIDTH
        right = (end_x - 1) // MAP_WIDTH
        top = start_y // MAP_HEIGHT
        bottom = (end_y - 1) // MAP_HEIGHT

        return (
            (sx, sy)
            for sy in range(top, bottom + 1)
            for sx in range(left, right + 1)
        )

    def build_viewport(
        self,
        player: "Player",
        *,
        width: int = SCREEN_WIDTH,
        height: int = SCREEN_HEIGHT,
    ) -> "ViewportData":
        world_x = player.screen_x * MAP_WIDTH + player.x
        world_y = player.screen_y * MAP_HEIGHT + player.y
        camera_x = world_x - width // 2
        camera_y = world_y - height // 2
        camera_x, camera_y = self._clamp_camera(camera_x, camera_y, width, height)

        tiles: list[list[dict]] = []
        for local_y in range(height):
            row: list[dict] = []
            world_y_coord = camera_y + local_y
            screen_y = world_y_coord // MAP_HEIGHT
            tile_y = world_y_coord % MAP_HEIGHT
            for local_x in range(width):
                world_x_coord = camera_x + local_x
                screen_x = world_x_coord // MAP_WIDTH
                tile_x = world_x_coord % MAP_WIDTH
                screen = self.screens[(screen_x, screen_y)]
                row.append(screen.terrain[tile_y][tile_x])
            tiles.append(row)

        footprints: list[tuple[int, int, dict]] = []
        enemies: list[tuple[Enemy, int, int]] = []
        characters: list[tuple[Character, int, int]] = []

        for screen_coords in self._screens_in_rect(camera_x, camera_y, width, height):
            screen = self.screens[screen_coords]
            base_x = screen_coords[0] * MAP_WIDTH
            base_y = screen_coords[1] * MAP_HEIGHT

            footprint_tile = screen.tiles.get("footprint")
            if footprint_tile:
                for fx, fy in player.get_footprints(screen_coords):
                    world_fx = base_x + fx
                    world_fy = base_y + fy
                    if camera_x <= world_fx < camera_x + width and camera_y <= world_fy < camera_y + height:
                        footprints.append(
                            (world_fx - camera_x, world_fy - camera_y, footprint_tile)
                        )

            for enemy in screen.enemies:
                if enemy and not getattr(enemy, "defeated", False):
                    world_ex = base_x + enemy.x
                    world_ey = base_y + enemy.y
                    if camera_x <= world_ex < camera_x + width and camera_y <= world_ey < camera_y + height:
                        enemies.append((enemy, world_ex - camera_x, world_ey - camera_y))

            for character in screen.characters:
                world_cx = base_x + character.x
                world_cy = base_y + character.y
                if camera_x <= world_cx < camera_x + width and camera_y <= world_cy < camera_y + height:
                    characters.append(
                        (character, world_cx - camera_x, world_cy - camera_y)
                    )

        player_view_x = world_x - camera_x
        player_view_y = world_y - camera_y

        return ViewportData(
            tiles=tiles,
            player_position=(player_view_x, player_view_y),
            camera=(camera_x, camera_y),
            enemies=enemies,
            characters=characters,
            footprints=footprints,
        )


@dataclass
class ViewportData:
    tiles: list[list[dict]]
    player_position: tuple[int, int]
    camera: tuple[int, int]
    enemies: list[tuple[Enemy, int, int]]
    characters: list[tuple[Character, int, int]]
    footprints: list[tuple[int, int, dict]]


def biome_for_row(row_index: int) -> str:
    top_threshold = WORLD_ROWS / 3
    bottom_threshold = (2 * WORLD_ROWS) / 3

    if row_index < top_threshold:
        return "winter"
    if row_index < bottom_threshold:
        return "summer"
    return "drought"


def find_spawn(game_map: Iterable[Iterable[dict]]) -> tuple[int, int]:
    """Find a walkable tile near the centre of the map."""

    cx, cy = MAP_WIDTH // 2, MAP_HEIGHT // 2
    if game_map[cy][cx]["walkable"]:
        return cx, cy

    for r in range(1, max(MAP_WIDTH, MAP_HEIGHT)):
        for y in range(max(0, cy - r), min(MAP_HEIGHT, cy + r + 1)):
            for x in range(max(0, cx - r), min(MAP_WIDTH, cx + r + 1)):
                if game_map[y][x]["walkable"]:
                    return x, y
    return 0, 0


def find_random_walkable(
    game_map, exclude: Iterable[tuple[int, int]] | None = None
) -> tuple[int, int]:
    width = len(game_map[0])
    height = len(game_map)
    exclude_set = set(exclude or [])
    attempts = 0
    while attempts < 500:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if (x, y) in exclude_set:
            attempts += 1
            continue
        if game_map[y][x]["walkable"]:
            return x, y
        attempts += 1
    return 0, 0


def _enemy_id_for_biome(biome: str) -> str:
    if biome == "winter":
        return "living_snow"
    return "stinky_forest_toad"


def build_world() -> World:
    biome_cache: Dict[str, BiomeDefinition] = {}
    screens: Dict[tuple[int, int], WorldScreen] = {}

    for sy in range(WORLD_ROWS):
        for sx in range(WORLD_COLUMNS):
            biome = biome_for_row(sy)
            biome_definition = biome_cache.setdefault(
                biome, get_biome_definition(biome)
            )
            coords = (sx, sy)
            terrain = generate_map(MAP_WIDTH, MAP_HEIGHT, biome_definition)
            enemy_id = _enemy_id_for_biome(biome)
            enemy_data = ENEMIES[enemy_id]
            enemies = []
            characters: list[Character] = []

            ex, ey = find_random_walkable(terrain)
            if terrain[ey][ex]["walkable"]:
                enemies.append(
                    Enemy(
                        name=enemy_data["name"],
                        char=enemy_data["char"],
                        fg=enemy_data["fg"],
                        bg=enemy_data["bg"],
                        max_hp=enemy_data["hp"],
                        attack_min=enemy_data["attack_min"],
                        attack_max=enemy_data["attack_max"],
                        reward_talents=enemy_data["reward_talents"],
                        stats=enemy_data["stats"],
                        x=ex,
                        y=ey,
                        screen_x=sx,
                        screen_y=sy,
                        tile_key=enemy_data.get("tile"),
                    )
                )

            screens[coords] = WorldScreen(
                tiles=biome_definition.tiles,
                terrain=terrain,
                biome=biome,
                enemies=enemies,
                characters=characters,
            )

    warlock_data = CHARACTERS["warlock"]
    available_screens = list(screens.keys())
    random.shuffle(available_screens)
    warlock_spawns = available_screens[: min(5, len(available_screens))]

    for screen_coords in warlock_spawns:
        screen = screens[screen_coords]
        occupied = [(enemy.x, enemy.y) for enemy in screen.enemies]
        occupied.extend((character.x, character.y) for character in screen.characters)
        wx, wy = find_random_walkable(screen.terrain, exclude=occupied)
        if not screen.terrain[wy][wx]["walkable"]:
            continue
        screen.characters.append(
            Character(
                name=warlock_data["name"],
                char=warlock_data["char"],
                fg=warlock_data["fg"],
                bg=warlock_data["bg"],
                stats=warlock_data["stats"],
                x=wx,
                y=wy,
                screen_x=screen_coords[0],
                screen_y=screen_coords[1],
                tile_key=warlock_data.get("tile"),
            )
        )

    spawn_screen = (WORLD_COLUMNS // 2, WORLD_ROWS // 2)
    spawn_map = screens[spawn_screen].terrain
    spawn_position = find_spawn(spawn_map)

    screen_enemies = screens[spawn_screen].enemies
    for enemy in screen_enemies:
        if (enemy.x, enemy.y) == spawn_position:
            new_x, new_y = find_random_walkable(
                spawn_map, exclude=[spawn_position]
            )
            if spawn_map[new_y][new_x]["walkable"]:
                enemy.x = new_x
                enemy.y = new_y
            else:
                enemy.defeated = True

    return World(
        screens=screens,
        spawn_screen=spawn_screen,
        spawn_position=spawn_position,
    )
