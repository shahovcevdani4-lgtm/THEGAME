# engine/ui.py
from __future__ import annotations

from textwrap import wrap

import tcod
from tcod.event import KeySym

from engine.inventory import build_inventory_context

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
    tiles,
    player,
    player_position,
    *,
    enemies=None,
    characters=None,
    hide_enemies=False,
    footprints=None,
):
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            console.print(x, y, tile["char"], fg=tile["fg"], bg=tile["bg"])

    if footprints:
        for fx, fy, footprint_tile in footprints:
            if 0 <= fy < console.height and 0 <= fx < console.width:
                console.print(
                    fx,
                    fy,
                    footprint_tile["char"],
                    fg=footprint_tile["fg"],
                    bg=footprint_tile["bg"],
                )

    if enemies and not hide_enemies:
        for enemy, ex, ey in enemies:
            if enemy and not getattr(enemy, "defeated", False):
                console.print(ex, ey, enemy.char, fg=enemy.fg, bg=enemy.bg)

    if characters:
        for character, cx, cy in characters:
            console.print(
                cx,
                cy,
                character.char,
                fg=character.fg,
                bg=character.bg,
            )

    px, py = player_position
    if 0 <= py < len(tiles) and 0 <= px < len(tiles[py]):
        player_tile_bg = tiles[py][px]["bg"]
    else:
        player_tile_bg = (0, 0, 0)
    console.print(
        px,
        py,
        player.tile["char"],
        fg=player.tile["fg"],
        bg=player_tile_bg,
    )

def show_class_menu(console, context, classes):
    lines = ["Выбери класс:", ""]
    for i, (cid, cls) in enumerate(classes.items(), start=1):
        lines.append(
            f"[{i}] {cls['name']} (STR {cls['str']} / AGI {cls['agi']} / INT {cls['int']})"
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


def draw_battle_ui(console, battle, talents_label: str):
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
    lines.extend(["", talents_label])

    draw_text_window(console, lines, padding=2)
def draw_inventory(console, player, talents_label: str) -> None:
    inventory = player.inventory

    padding = 1
    slot_width = 3
    horizontal_gap = 1
    columns = inventory.columns
    grid_width = columns * slot_width + (columns - 1) * horizontal_gap

    content_lines = 4 + inventory.passive_rows
    frame_width = grid_width + 2 * padding + 2
    frame_height = content_lines + 2 * padding + 2

    context_lines = build_inventory_context(player, talents_label)
    panel_height = min(console.height // 2, max(6, len(context_lines) + 2))
    available_height = console.height - panel_height

    start_x = max(0, (console.width - frame_width) // 2)
    start_y = max(0, (available_height - frame_height) // 2)

    console.draw_frame(
        start_x,
        start_y,
        frame_width,
        frame_height,
        fg=(200, 200, 200),
        bg=(20, 20, 20),
        clear=False,
    )

    text_x = start_x + padding + 1
    text_y = start_y + padding + 1
    console.print(text_x, text_y, "Активные слоты:", fg=(180, 200, 255), bg=(20, 20, 20))

    slot_base_y = text_y + 1
    for index, slot_name in enumerate(inventory.ACTIVE_SLOT_ORDER):
        slot_char = inventory.active_slot_symbol(slot_name)
        slot_x = text_x + index * (slot_width + horizontal_gap)
        slot_index = index
        is_selected = slot_index == inventory.cursor_index
        is_two_handed = inventory.is_two_handed_slot(slot_name)
        bg = (90, 70, 120) if is_selected else (55, 55, 80)
        if is_two_handed and not is_selected:
            bg = (70, 50, 90)
        console.print(slot_x, slot_base_y, f"[{slot_char}]", fg=(230, 230, 230), bg=bg)

    passive_label_y = slot_base_y + 2
    console.print(text_x, passive_label_y, "Пассивные слоты:", fg=(180, 200, 255), bg=(20, 20, 20))

    grid_start_y = passive_label_y + 1
    for row in range(inventory.passive_rows):
        for col in range(columns):
            slot_index = len(inventory.ACTIVE_SLOT_ORDER) + row * columns + col
            passive_index = slot_index - len(inventory.ACTIVE_SLOT_ORDER)
            slot_char = inventory.passive_slot_symbol(passive_index)
            slot_x = text_x + col * (slot_width + horizontal_gap)
            slot_y = grid_start_y + row
            is_selected = slot_index == inventory.cursor_index
            bg = (90, 70, 120) if is_selected else (40, 40, 60)
            console.print(slot_x, slot_y, f"[{slot_char}]", fg=(220, 220, 220), bg=bg)

    _draw_inventory_context(console, context_lines, panel_height)


def _draw_inventory_context(
    console, context_lines: list[tuple[str, tuple[int, int, int]]], panel_height: int
) -> None:
    start_y = console.height - panel_height
    console.draw_rect(
        0,
        start_y,
        console.width,
        panel_height,
        ch=32,
        fg=(180, 180, 200),
        bg=(15, 15, 35),
    )

    max_lines = panel_height - 1
    for offset, (text, color) in enumerate(context_lines[:max_lines]):
        console.print(2, start_y + offset + 1, text, fg=color, bg=(15, 15, 35))
