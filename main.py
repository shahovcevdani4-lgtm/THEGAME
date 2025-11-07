# main.py
import os
from pathlib import Path
import tcod
from tcod.event import KeySym

from data.classes import CLASSES
from engine.mapgen import generate_map
from engine.player import Player
from engine.ui import draw_map, show_class_menu

# размеры карты и окна (под tileset 10x10 — 40x25 хорошо помещается)
MAP_WIDTH = 40
MAP_HEIGHT = 25
SCREEN_WIDTH = MAP_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT

FONT_FILE = "dejavu10x10_gs_tc.png"  # можно заменить или удалить — см. try/except ниже

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

def main():
    # Пытаемся загрузить красивый шрифт; если его нет — идём с дефолтом
    tileset = None
    if Path(FONT_FILE).exists():
        tileset = tcod.tileset.load_tilesheet(
            FONT_FILE, 32, 8, tcod.tileset.CHARMAP_TCOD
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
        player = Player(sx, sy)

        # Игровой цикл
        while True:
            console.clear()
            draw_map(console, game_map, player)

            # строка статусов (кратко показываем выбранный класс и статы)
            info = f"{chosen_class['name']} | STR {chosen_class['str']}  DEX {chosen_class['dex']}  INT {chosen_class['int']}"
            console.print(0, 0, info)

            context.present(console)

            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()
                elif event.type == "KEYDOWN":
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
                        player.move(dx, dy, game_map)

if __name__ == "__main__":
    main()
