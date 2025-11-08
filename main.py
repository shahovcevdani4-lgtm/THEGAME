# main.py
from __future__ import annotations

import tcod
from tcod.event import KeySym

from data.classes import CLASSES
from engine.assets import load_preferred_tileset
from engine.battle import Battle
from engine.constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_COLUMNS,
    WORLD_ROWS,
)
from engine.player import Player
from engine.ui import (
    draw_battle_ui,
    draw_inventory,
    draw_map,
    show_class_menu,
)
from engine.world import build_world


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

        chosen_id = show_class_menu(console, context, CLASSES)
        chosen_class = CLASSES[chosen_id]

        world = build_world()
        spawn_screen = world.spawn_screen
        spawn_x, spawn_y = world.spawn_position

        player = Player(
            spawn_x,
            spawn_y,
            stats=chosen_class,
            screen_x=spawn_screen[0],
            screen_y=spawn_screen[1],
        )

        current_battle: Battle | None = None
        inventory_open = False

        while True:
            console.clear()
            current_screen = (player.screen_x, player.screen_y)
            world_screen = world.get_screen(current_screen)
            game_map = world_screen.terrain
            footprints = player.get_footprints(current_screen)
            footprint_tile = world_screen.tiles.get("footprint")
            draw_map(
                console,
                game_map,
                player,
                enemies=world_screen.enemies,
                hide_enemies=current_battle is not None,
                footprints=footprints,
                footprint_tile=footprint_tile,
            )

            info = (
                f"{chosen_class['name']} | STR {player.strength}  DEX {player.dexterity}  INT {player.intelligence}"
            )
            console.print(0, 0, info)

            talents_label = f"Золотые таланты: {player.talents}"

            if current_battle:
                draw_battle_ui(console, current_battle, talents_label)
            elif inventory_open:
                draw_inventory(console, player.inventory, talents_label)

            context.present(console)

            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()
                if event.type != "KEYDOWN":
                    continue

                if event.sym == KeySym.ESCAPE:
                    raise SystemExit()

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

                    if handled and current_battle.finished:
                        if current_battle.result == "defeat":
                            context.present(console)
                            raise SystemExit("Вы пали в бою.")
                        if current_battle.result in {"victory", "bribe", "run"}:
                            enemy_screen = (
                                current_battle.enemy.screen_x,
                                current_battle.enemy.screen_y,
                            )
                            screen_enemies = world.enemies_at(enemy_screen)
                            if current_battle.result == "run":
                                current_battle.enemy.hp = current_battle.enemy.max_hp
                                (
                                    prev_screen_x,
                                    prev_screen_y,
                                    prev_x,
                                    prev_y,
                                ) = current_battle.previous_state
                                player.set_position(prev_screen_x, prev_screen_y, prev_x, prev_y)
                            else:
                                if current_battle.enemy in screen_enemies:
                                    screen_enemies.remove(current_battle.enemy)
                        current_battle = None
                    break

                if inventory_open:
                    if event.sym == KeySym.I:
                        inventory_open = False
                    elif event.sym == KeySym.W:
                        player.inventory.move_cursor(0, -1)
                    elif event.sym == KeySym.S:
                        player.inventory.move_cursor(0, 1)
                    elif event.sym == KeySym.A:
                        player.inventory.move_cursor(-1, 0)
                    elif event.sym == KeySym.D:
                        player.inventory.move_cursor(1, 0)
                    break

                if event.sym == KeySym.I:
                    inventory_open = True
                    break

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

                if dx == 0 and dy == 0:
                    break

                previous_state = player.position()
                previous_screen_coords = (player.screen_x, player.screen_y)
                previous_tile = (player.x, player.y)

                current_map = world.map_at(previous_screen_coords)
                new_x = player.x + dx
                new_y = player.y + dy
                screen_dx = 0
                screen_dy = 0
                blocked = False

                if new_x < 0:
                    if player.screen_x > 0:
                        screen_dx = -1
                        new_x = len(current_map[0]) - 1
                    else:
                        blocked = True
                elif new_x >= len(current_map[0]):
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
                        new_y = len(current_map) - 1
                    else:
                        blocked = True
                elif new_y >= len(current_map):
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
                    if target_screen == previous_screen_coords
                    else world.map_at(target_screen)
                )

                if not target_map[new_y][new_x]["walkable"]:
                    break

                if target_screen != previous_screen_coords:
                    player.set_position(target_screen[0], target_screen[1], new_x, new_y)
                else:
                    player.x = new_x
                    player.y = new_y

                if world.biome_at(previous_screen_coords) == "winter":
                    player.leave_footprint(previous_screen_coords, previous_tile)

                current_screen_enemies = world.enemies_at((player.screen_x, player.screen_y))
                for enemy in current_screen_enemies:
                    if (
                        not enemy.defeated
                        and player.x == enemy.x
                        and player.y == enemy.y
                    ):
                        current_battle = Battle(player, enemy, previous_state)
                        inventory_open = False
                        break
                break


if __name__ == "__main__":
    main()
