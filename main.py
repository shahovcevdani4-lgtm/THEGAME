# main.py
import os
from pathlib import Path
from typing import Iterator, Tuple

import tcod
from tcod.event import KeySym

from data.classes import CLASSES
from data.enemies import ENEMIES
from engine.battle import Battle, Enemy
from data.tiles import get_biome_tiles
from engine.mapgen import generate_map
from engine.player import Player
from engine.ui import draw_battle_ui, draw_map, show_class_menu

# размеры карты и окна (под tileset 10x10 — 40x25 хорошо помещается)
MAP_WIDTH = 40
MAP_HEIGHT = 25
SCREEN_WIDTH = MAP_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT

WORLD_COLUMNS = 8
WORLD_ROWS = 4
TOTAL_SCREENS = WORLD_COLUMNS * WORLD_ROWS
assert TOTAL_SCREENS == 32

FONT_ENV_VAR = "ROGUELIKE_FONT"
FONT_PRIORITY = (
    Path("data/fonts/main.ttf"),
    Path("data/fonts/main.otf"),
    Path("dejavu10x10_gs_tc.png"),
)


def load_tileset(font_file: "str | os.PathLike[str]") -> "tcod.tileset.Tileset | None":
    """Загрузить тайлсет, поддерживая как PNG, так и TTF/OTF."""

    path = Path(font_file)
    if not path.exists():
        return None

    suffix = path.suffix.lower()
    try:
        if suffix == ".png":
            return tcod.tileset.load_tilesheet(
                str(path), 32, 8, tcod.tileset.CHARMAP_TCOD
            )
        if suffix in {".ttf", ".otf"}:
            return tcod.tileset.load_truetype_font(
                str(path), 32, 8, charmap=tcod.tileset.CHARMAP_TCOD
            )
    except Exception as exc:  # pragma: no cover - выводим предупреждение в консоль
        print(f"Не удалось загрузить шрифт {path}: {exc}")
    return None


def iter_font_candidates() -> Iterator[Path]:
    """Перечислить пути к шрифтам в порядке приоритета."""

    override = os.environ.get(FONT_ENV_VAR)
    if override:
        yield Path(override)
    for candidate in FONT_PRIORITY:
        yield Path(candidate)


def load_preferred_tileset() -> Tuple["tcod.tileset.Tileset | None", Path | None]:
    """Подобрать подходящий шрифт, учитывая override и стандартные пути."""

    for candidate in iter_font_candidates():
        tileset = load_tileset(candidate)
        if tileset is not None:
            return tileset, candidate
    return None, None


def biome_for_row(row_index: int) -> str:
    top_threshold = WORLD_ROWS / 3
    bottom_threshold = (2 * WORLD_ROWS) / 3

    if row_index < top_threshold:
        return "winter"
    if row_index < bottom_threshold:
        return "summer"
    return "drought"

def find_spawn(game_map):
    """Найти проходимую клетку, стараясь ближе к центру."""
    cx, cy = MAP_WIDTH // 2, MAP_HEIGHT // 2
    if game_map[cy][cx]["walkable"]:
        return cx, cy
    # если центр занят — простой поиск по спирали
    for r in range(1, max(MAP_WIDTH, MAP_HEIGHT)):
        for y in range(max(0, cy - r), min(MAP_HEIGHT, cy + r + 1)):
            for x in range(max(0, cx - r), min(MAP_WIDTH, cx + r + 1)):
                if game_map[y][x]["walkable"]:
                    return x, y
    return 0, 0  # на всякий случай

def find_random_walkable(game_map, exclude=None):
    import random

    width = len(game_map[0])
    height = len(game_map)
    exclude = set(exclude or [])
    attempts = 0
    while attempts < 500:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if (x, y) in exclude:
            attempts += 1
            continue
        if game_map[y][x]["walkable"]:
            return x, y
        attempts += 1
    return 0, 0


def build_world():
    tile_cache: dict[str, dict] = {}
    world_maps: dict[tuple[int, int], list[list[dict]]] = {}
    screen_tiles: dict[tuple[int, int], dict] = {}
    biomes: dict[tuple[int, int], str] = {}

    for sy in range(WORLD_ROWS):
        for sx in range(WORLD_COLUMNS):
            biome = biome_for_row(sy)
            palette = tile_cache.setdefault(biome, get_biome_tiles(biome))
            coords = (sx, sy)
            world_maps[coords] = generate_map(MAP_WIDTH, MAP_HEIGHT, palette)
            screen_tiles[coords] = palette
            biomes[coords] = biome

    spawn_screen = (WORLD_COLUMNS // 2, WORLD_ROWS // 2)
    spawn_map = world_maps[spawn_screen]
    spawn_x, spawn_y = find_spawn(spawn_map)

    enemies_by_screen: dict[tuple[int, int], list[Enemy]] = {}
    toad_data = ENEMIES["stinky_forest_toad"]

    for coords, local_map in world_maps.items():
        exclude = {(spawn_x, spawn_y)} if coords == spawn_screen else set()
        ex, ey = find_random_walkable(local_map, exclude=exclude)
        if (
            0 <= ex < MAP_WIDTH
            and 0 <= ey < MAP_HEIGHT
            and local_map[ey][ex]["walkable"]
        ):
            enemy = Enemy(
                name=toad_data["name"],
                char=toad_data["char"],
                fg=toad_data["fg"],
                bg=toad_data["bg"],
                max_hp=toad_data["hp"],
                attack_min=toad_data["attack_min"],
                attack_max=toad_data["attack_max"],
                reward_talents=toad_data["reward_talents"],
                stats=toad_data["stats"],
                x=ex,
                y=ey,
                screen_x=coords[0],
                screen_y=coords[1],
            )
            enemies_by_screen[coords] = [enemy]
        else:
            enemies_by_screen[coords] = []

    return (
        world_maps,
        screen_tiles,
        biomes,
        enemies_by_screen,
        spawn_screen,
        (spawn_x, spawn_y),
    )


def main():
    # Пытаемся подобрать шрифт в порядке приоритета; если не нашли — идём с дефолтом
    tileset, used_font = load_preferred_tileset()
    if used_font is not None:
        print(f"Используем шрифт: {used_font}")
    else:
        print(
            "Не удалось найти подходящий шрифт в data/fonts/ — будет использован стандартный tileset."
        )

    with tcod.context.new_terminal(
        columns=SCREEN_WIDTH,
        rows=SCREEN_HEIGHT,
        tileset=tileset,
        title="ASCII Roguelike — прототип",
        vsync=True,
    ) as context:
        console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")

        # Меню выбора класса
        chosen_id = show_class_menu(console, context, CLASSES)
        chosen_class = CLASSES[chosen_id]
        # (пока просто фиксируем выбор; позже сюда подвяжем расчёт HP/урона и т.д.)

        (
            world_maps,
            screen_tiles,
            biomes,
            enemies_by_screen,
            spawn_screen,
            (spawn_x, spawn_y),
        ) = build_world()

        player = Player(
            spawn_x,
            spawn_y,
            stats=chosen_class,
            screen_x=spawn_screen[0],
            screen_y=spawn_screen[1],
        )

        current_battle = None

        # Игровой цикл
        while True:
            console.clear()
            talents_text = f"Talents: {player.talents}"
            current_screen = (player.screen_x, player.screen_y)
            game_map = world_maps[current_screen]
            footprints = player.get_footprints(current_screen)
            footprint_tile = screen_tiles[current_screen].get("footprint")
            draw_map(
                console,
                game_map,
                player,
                enemies=enemies_by_screen.get(current_screen, []),
                hide_enemies=current_battle is not None,
                footprints=footprints,
                footprint_tile=footprint_tile,
            )

            # строка статусов (кратко показываем выбранный класс и статы)
            info = (
                f"{chosen_class['name']} | STR {player.strength}  DEX {player.dexterity}  INT {player.intelligence}"
            )
            console.print(0, 0, info)

            if current_battle:
                draw_battle_ui(console, current_battle, talents_text)
            else:
                console.print(
                    SCREEN_WIDTH - len(talents_text),
                    SCREEN_HEIGHT - 1,
                    talents_text,
                    fg=(255, 255, 0),
                )

            context.present(console)

            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()
                elif event.type == "KEYDOWN":
                    if current_battle:
                        handled = False
                        if event.sym in (KeySym.N1, KeySym.KP_1):
                            current_battle.attack_round()
                            handled = True
                        elif event.sym in (KeySym.N2, KeySym.KP_2):
                            current_battle.run_away()
                            handled = True
                        elif event.sym in (KeySym.N3, KeySym.KP_3):
                            current_battle.bribe()
                            handled = True
                        elif event.sym == KeySym.ESCAPE:
                            raise SystemExit()

                        if handled and current_battle.finished:
                            if current_battle.result == "defeat":
                                context.present(console)
                                raise SystemExit("Вы пали в бою.")
                            if current_battle.result in {"victory", "bribe", "run"}:
                                enemy_screen = (
                                    current_battle.enemy.screen_x,
                                    current_battle.enemy.screen_y,
                                )
                                screen_enemies = enemies_by_screen.get(enemy_screen, [])
                                if current_battle.result == "run":
                                    current_battle.enemy.hp = current_battle.enemy.max_hp
                                    prev_screen_x, prev_screen_y, prev_x, prev_y = (
                                        current_battle.previous_state
                                    )
                                    player.set_position(
                                        prev_screen_x, prev_screen_y, prev_x, prev_y
                                    )
                                else:
                                    if current_battle.enemy in screen_enemies:
                                        screen_enemies.remove(current_battle.enemy)
                            current_battle = None
                        break

                    else:
                        dx = 0
                        dy = 0
                        if event.sym == KeySym.W:
                            dy = -1
                        elif event.sym == KeySym.S:
                            dy = 1
                        elif event.sym == KeySym.A:
                            dx = -1
                        elif event.sym == KeySym.D:
                            dx = 1
                        elif event.sym == KeySym.ESCAPE:
                            raise SystemExit()

                        if dx or dy:
                            current_screen = (player.screen_x, player.screen_y)
                            current_map = world_maps[current_screen]
                            new_x = player.x + dx
                            new_y = player.y + dy
                            screen_dx = 0
                            screen_dy = 0
                            blocked = False

                            if new_x < 0:
                                if player.screen_x > 0:
                                    screen_dx = -1
                                    new_x = MAP_WIDTH - 1
                                else:
                                    blocked = True
                            elif new_x >= MAP_WIDTH:
                                if player.screen_x < WORLD_COLUMNS - 1:
                                    screen_dx = 1
                                    new_x = 0
                                else:
                                    blocked = True

                            if blocked:
                                break

                            if new_y < 0:
                                if player.screen_y > 0:
                                    screen_dy = -1
                                    new_y = MAP_HEIGHT - 1
                                else:
                                    blocked = True
                            elif new_y >= MAP_HEIGHT:
                                if player.screen_y < WORLD_ROWS - 1:
                                    screen_dy = 1
                                    new_y = 0
                                else:
                                    blocked = True

                            if blocked:
                                break

                            target_screen = (
                                player.screen_x + screen_dx,
                                player.screen_y + screen_dy,
                            )
                            target_map = (
                                current_map
                                if target_screen == current_screen
                                else world_maps.get(target_screen)
                            )

                            if target_map is None:
                                break

                            if not target_map[new_y][new_x]["walkable"]:
                                break

                            previous_state = player.position()
                            previous_screen_coords = (player.screen_x, player.screen_y)
                            previous_tile = (player.x, player.y)

                            if target_screen != current_screen:
                                player.set_position(
                                    target_screen[0], target_screen[1], new_x, new_y
                                )
                            else:
                                player.x = new_x
                                player.y = new_y

                            if biomes[previous_screen_coords] == "winter":
                                player.leave_footprint(previous_screen_coords, previous_tile)

                            current_screen_enemies = enemies_by_screen.get(
                                (player.screen_x, player.screen_y), []
                            )
                            for enemy in current_screen_enemies:
                                if (
                                    not enemy.defeated
                                    and player.x == enemy.x
                                    and player.y == enemy.y
                                ):
                                    current_battle = Battle(
                                        player, enemy, previous_state
                                    )
                                    break
                        break

if __name__ == "__main__":
    main()
