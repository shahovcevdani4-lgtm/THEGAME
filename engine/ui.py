# engine/ui.py
import tcod
from tcod.event import KeySym

WINDOW_BG = (0, 0, 0)
WINDOW_TEXT = (210, 210, 210)


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


def _center_window(console, width, height):
    x = max(0, (console.width - width) // 2)
    y = max(0, (console.height - height) // 2)
    return x, y


def draw_text_window(console, lines, padding=1, fg=WINDOW_TEXT, bg=WINDOW_BG):
    if not lines:
        return 0, 0, 0, 0

    max_line = max(len(line) for line in lines)
    width = min(console.width, max(10, max_line + padding * 2))
    inner_height = len(lines)
    height = min(console.height, inner_height + padding * 2)

    x, y = _center_window(console, width, height)
    console.draw_rect(
        x,
        y,
        width,
        height,
        ch=32,
        fg=fg,
        bg=bg,
        bg_blend=tcod.BKGND_SET,
    )

    visible_lines = lines[: height - padding * 2]
    if visible_lines:
        console.print_box(
            x + padding,
            y + padding,
            max(1, width - padding * 2),
            max(1, height - padding * 2),
            "\n".join(visible_lines),
            fg=fg,
            bg=bg,
        )
    return x, y, width, height


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
    padding_x = 2
    padding_y = 1
    log_lines = battle.log[-6:]
    content_lines = [
        battle.enemy.name,
        f"HP: {battle.enemy.hp}/{battle.enemy.max_hp}",
        "1) Battle  2) Run away  3) Bribe",
        f"(Откуп: {battle.bribe_cost()} талантов)",
        f"Ваше здоровье: {battle.player.hp}/{battle.player.max_hp}",
        "Журнал:",
        *log_lines,
        talents_text,
    ]
    max_line_length = max(len(line) for line in content_lines) if content_lines else 0
    panel_width = min(console.width - 2, max(32, max_line_length + padding_x * 2))
    panel_height = min(console.height - 2, len(log_lines) + 13)
    x, y = _center_window(console, panel_width, panel_height)

    console.draw_rect(
        x,
        y,
        panel_width,
        panel_height,
        ch=32,
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
        bg_blend=tcod.BKGND_SET,
    )

    sprite_y = y + padding_y
    console.print(
        x + panel_width // 2,
        sprite_y,
        battle.enemy.char,
        fg=battle.enemy.fg,
        bg=battle.enemy.bg,
        alignment=tcod.CENTER,
    )

    line_y = sprite_y + 1
    line_x = x + padding_x

    console.print(line_x, line_y, battle.enemy.name, fg=WINDOW_TEXT, bg=WINDOW_BG)
    line_y += 1
    console.print(
        line_x,
        line_y,
        f"HP: {battle.enemy.hp}/{battle.enemy.max_hp}",
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )
    line_y += 1
    line_y += 1

    console.print(
        line_x,
        line_y,
        "1) Battle  2) Run away  3) Bribe",
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )
    line_y += 1
    console.print(
        line_x,
        line_y,
        f"(Откуп: {battle.bribe_cost()} талантов)",
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )
    line_y += 1
    line_y += 1

    console.print(
        line_x,
        line_y,
        f"Ваше здоровье: {battle.player.hp}/{battle.player.max_hp}",
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )
    line_y += 1
    console.print(
        line_x,
        line_y,
        "Порядок хода: "
        + (
            "игрок" if battle.player.average_power() >= battle.enemy.average_power() else "враг"
        )
        + " первым",
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )
    line_y += 1
    line_y += 1

    console.print(line_x, line_y, "Журнал:", fg=WINDOW_TEXT, bg=WINDOW_BG)
    line_y += 1

    log_height = max(1, (y + panel_height - padding_y - 1) - line_y)
    console.print_box(
        line_x,
        line_y,
        max(1, panel_width - padding_x * 2),
        log_height,
        "\n".join(log_lines),
        fg=WINDOW_TEXT,
        bg=WINDOW_BG,
    )

    talents_y = y + panel_height - padding_y - 1
    console.print(
        x + panel_width - padding_x - len(talents_text),
        talents_y,
        talents_text,
        fg=(255, 255, 0),
        bg=WINDOW_BG,
    )
