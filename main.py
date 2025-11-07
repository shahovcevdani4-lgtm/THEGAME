# main.py
import os
from pathlib import Path
from typing import Iterator, Tuple

import tcod
from tcod.event import KeySym

from data.classes import CLASSES
from data.enemies import ENEMIES
from engine.battle import Battle, Enemy
from engine.mapgen import generate_map
from engine.player import Player
from engine.ui import draw_battle_ui, draw_map, show_class_menu

# размеры карты и окна (под tileset 10x10 — 40x25 хорошо помещается)
MAP_WIDTH = 40
MAP_HEIGHT = 25
SCREEN_WIDTH = MAP_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT

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
                str(path), 32, 8, tcod.tileset.CHARMAP_TCOD
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

        # Генерация карты
        game_map = generate_map(MAP_WIDTH, MAP_HEIGHT)

        # Спавн игрока
        sx, sy = find_spawn(game_map)
        player = Player(sx, sy, stats=chosen_class)

        enemies = []
        ex, ey = find_random_walkable(game_map, exclude={(player.x, player.y)})
        toad_data = ENEMIES["stinky_forest_toad"]
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
        )
        enemies.append(enemy)

        current_battle = None

        # Игровой цикл
        while True:
            console.clear()
            talents_text = f"Talents: {player.talents}"
            draw_map(
                console,
                game_map,
                player,
                enemies=enemies,
                hide_enemies=current_battle is not None,
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
                                if current_battle.enemy in enemies:
                                    if current_battle.result == "run":
                                        current_battle.enemy.hp = current_battle.enemy.max_hp
                                        player.x, player.y = current_battle.previous_position
                                    else:
                                        enemies.remove(current_battle.enemy)
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
                            previous_position = (player.x, player.y)
                            moved = player.move(dx, dy, game_map)
                            if moved:
                                for enemy in enemies:
                                    if not enemy.defeated and player.x == enemy.x and player.y == enemy.y:
                                        current_battle = Battle(player, enemy, previous_position)
                                        break
                        break

if __name__ == "__main__":
    main()
