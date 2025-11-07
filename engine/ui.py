# engine/ui.py
from __future__ import annotations

from textwrap import wrap

import tcod
from tcod.event import KeySym


DEFAULT_TEXT_COLOR = (255, 255, 255)
DEFAULT_WINDOW_BG = (0, 0, 0)


def draw_text_window(
    console,
    lines,
    padding: int = 1,
    *,
    fg_color: tuple[int, int, int] = DEFAULT_TEXT_COLOR,
    bg_color: tuple[int, int, int] = DEFAULT_WINDOW_BG,
) -> None:
    """Отрисовать текстовое окно по центру консоли."""

    if not lines:
        return

    max_content_width = max(1, console.width - 2 * padding - 2)

    processed_lines = []
    for line in lines:
        if line == "":
            processed_lines.append("")
            continue
        wrapped = wrap(line, max_content_width) or [""]
        processed_lines.extend(wrapped)

    inner_width = min(max(len(line) for line in processed_lines), max_content_width)
    frame_width = inner_width + 2 * padding + 2
    frame_height = len(processed_lines) + 2 * padding + 2

    start_x = max(0, (console.width - frame_width) // 2)
    start_y = max(0, (console.height - frame_height) // 2)

    console.draw_frame(
        start_x,
        start_y,
        frame_width,
        frame_height,
        fg=fg_color,
        bg=bg_color,
        clear=False,
    )

    if frame_width > 2 and frame_height > 2:
        console.draw_rect(
            start_x + 1,
            start_y + 1,
            frame_width - 2,
            frame_height - 2,
            ch=32,
            fg=fg_color,
            bg=bg_color,
        )

    text_x = start_x + padding + 1
    text_y = start_y + padding + 1

    for i, line in enumerate(processed_lines):
        console.print(text_x, text_y + i, line, fg=fg_color, bg=bg_color)


def draw_map(
    console,
    game_map,
    player,
    *,
    enemies=None,
    hide_enemies=False,
    footprints=None,
    footprint_tile=None,
):
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            console.print(x, y, tile["char"], fg=tile["fg"], bg=tile["bg"])
    if footprints and footprint_tile:
        for fx, fy in footprints:
            if 0 <= fy < console.height and 0 <= fx < console.width:
                console.print(
                    fx,
                    fy,
                    footprint_tile["char"],
                    fg=footprint_tile["fg"],
                    bg=footprint_tile["bg"],
                )
    if enemies and not hide_enemies:
        for enemy in enemies:
            if enemy and not enemy.defeated:
                console.print(enemy.x, enemy.y, enemy.char, fg=enemy.fg, bg=enemy.bg)
    player_tile_bg = game_map[player.y][player.x]["bg"]
    console.print(
        player.x,
        player.y,
        player.tile["char"],
        fg=player.tile["fg"],
        bg=player_tile_bg,
    )

def show_class_menu(console, context, classes):
    lines = ["Выбери класс:", ""]
    for i, (cid, cls) in enumerate(classes.items(), start=1):
        lines.append(
            f"[{i}] {cls['name']} (STR {cls['str']} / DEX {cls['dex']} / INT {cls['int']})"
        )

    console.clear()
    draw_text_window(console, lines, padding=2)
    context.present(console)

    while True:
        for event in tcod.event.wait():
            if event.type == "KEYDOWN":
                if event.sym in (KeySym.N1, KeySym.KP_1):
                    return list(classes.keys())[0]
                if event.sym in (KeySym.N2, KeySym.KP_2):
                    return list(classes.keys())[1]


def draw_battle_ui(console, battle, talents_text: str):
    bribe_cost = battle.bribe_cost()
    turn_order = (
        "игрок" if battle.player.average_power() >= battle.enemy.average_power() else "враг"
    )

    lines = [
        f"{battle.enemy.char}  {battle.enemy.name}",
        f"HP врага: {battle.enemy.hp}/{battle.enemy.max_hp}",
        "",
        "Действия:",
        "1) Атака  2) Побег  3) Откуп",
        f"Стоимость откупа: {bribe_cost} талантов",
        "",
        f"Ваше здоровье: {battle.player.hp}/{battle.player.max_hp}",
        f"Ходит первым: {turn_order}",
        "",
        "Журнал боя:",
    ]

    lines.extend(battle.log[-6:] or ["..."])
    lines.extend(["", talents_text])

    draw_text_window(console, lines, padding=2)
