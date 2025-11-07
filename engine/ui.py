# engine/ui.py
import tcod
from tcod.event import KeySym

def draw_map(console, game_map, player):
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            console.print(x, y, tile["char"], fg=tile["fg"], bg=tile["bg"])
    console.print(player.x, player.y, player.tile["char"], fg=player.tile["fg"], bg=player.tile["bg"])

def show_class_menu(console, context, classes):
    console.clear()
    console.print(0, 0, "Выбери класс:")
    y = 2
    for i, (cid, cls) in enumerate(classes.items(), start=1):
        console.print(0, y, f"[{i}] {cls['name']} (STR {cls['str']} / DEX {cls['dex']} / INT {cls['int']})")
        y += 1
    context.present(console)

    while True:
        for event in tcod.event.wait():
            if event.type == "KEYDOWN":
                # новые enum-коды клавиш
                if event.sym in (KeySym.N1, KeySym.KP_1):
                    return list(classes.keys())[0]
                if event.sym in (KeySym.N2, KeySym.KP_2):
                    return list(classes.keys())[1]
