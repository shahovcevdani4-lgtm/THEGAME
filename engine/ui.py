# engine/ui.py
from __future__ import annotations

from textwrap import wrap

import tcod
from tcod.event import KeySym


def draw_text_window(console, lines, padding: int = 1) -> None:
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

    console.draw_frame(start_x, start_y, frame_width, frame_height, clear=False)

    text_x = start_x + padding + 1
    text_y = start_y + padding + 1

    for i, line in enumerate(processed_lines):
        console.print(text_x, text_y + i, line)


def draw_map(console, game_map, player, enemies=None, hide_enemies=False):
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            console.print(x, y, tile["char"], fg=tile["fg"], bg=tile["bg"])
    if enemies and not hide_enemies:
        for enemy in enemies:
            if enemy and not enemy.defeated:
                console.print(enemy.x, enemy.y, enemy.char, fg=enemy.fg, bg=enemy.bg)
    console.print(
        player.x,
        player.y,
        player.tile["char"],
        fg=player.tile["fg"],
        bg=player.tile["bg"],
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
    width = console.width
    info_y = 2

    # Enemy sprite area
    console.print(
        width // 2 - 1,
        info_y,
        battle.enemy.char,
        fg=battle.enemy.fg,
        bg=battle.enemy.bg,
    )

    console.print(0, info_y, f"{battle.enemy.name}")
    console.print(0, info_y + 1, f"HP: {battle.enemy.hp}/{battle.enemy.max_hp}")
    console.print(
        0,
        info_y + 3,
        "1) Battle  2) Run away  3) Bribe",
    )

    bribe_cost = battle.bribe_cost()
    console.print(0, info_y + 4, f"(Откуп: {bribe_cost} талантов)")

    console.print(
        0,
        info_y + 6,
        f"Ваше здоровье: {battle.player.hp}/{battle.player.max_hp}",
    )
    console.print(
        0,
        info_y + 7,
        f"Порядок хода: {'игрок' if battle.player.average_power() >= battle.enemy.average_power() else 'враг'} первым",
    )

    log_start = info_y + 9
    for i, message in enumerate(battle.log[-6:]):
        console.print(0, log_start + i, message)

    console.print(
        width - len(talents_text),
        console.height - 1,
        talents_text,
        fg=(255, 255, 0),
    )
