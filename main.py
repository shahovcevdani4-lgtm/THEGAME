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


USE_PYGAME = True


def run_ascii() -> None:
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
            name="Герой",
            character_class=chosen_class["name"],
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
                characters=world_screen.characters,
                hide_enemies=current_battle is not None,
                footprints=footprints,
                footprint_tile=footprint_tile,
            )

            talents_label = f"Золотые таланты: {player.talents}"

            if current_battle:
                draw_battle_ui(console, current_battle, talents_label)
            elif inventory_open:
                draw_inventory(console, player, talents_label)

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
                            elif current_battle.result == "bribe":
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
                    if event.sym in (KeySym.I, KeySym.i):
                        inventory_open = False
                        player.inventory.clear_message()
                    elif event.sym in (KeySym.W, KeySym.w):
                        player.inventory.move_cursor(0, -1)
                    elif event.sym in (KeySym.S, KeySym.s):
                        player.inventory.move_cursor(0, 1)
                    elif event.sym in (KeySym.A, KeySym.a):
                        player.inventory.move_cursor(-1, 0)
                    elif event.sym in (KeySym.D, KeySym.d):
                        player.inventory.move_cursor(1, 0)
                    elif event.sym in (KeySym.E, KeySym.e):
                        player.inventory.transfer_selected()
                    break

                if event.sym in (KeySym.I, KeySym.i):
                    inventory_open = True
                    player.inventory.clear_message()
                    break

                dx = 0
                dy = 0
                if event.sym in (KeySym.W, KeySym.w):
                    dy = -1
                elif event.sym in (KeySym.S, KeySym.s):
                    dy = 1
                elif event.sym in (KeySym.A, KeySym.a):
                    dx = -1
                elif event.sym in (KeySym.D, KeySym.d):
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


def run_pygame() -> None:
    from engine.graphics_pygame import PygameRenderer
    import pygame

    renderer = PygameRenderer()
    try:
        chosen_id = renderer.show_class_menu(CLASSES)
        chosen_class = CLASSES[chosen_id]

        world = build_world()
        spawn_screen = world.spawn_screen
        spawn_x, spawn_y = world.spawn_position

        player = Player(
            spawn_x,
            spawn_y,
            stats=chosen_class,
            name="Герой",
            character_class=chosen_class["name"],
            screen_x=spawn_screen[0],
            screen_y=spawn_screen[1],
        )

        current_battle: Battle | None = None
        inventory_open = False

        while True:
            renderer.clear()
            current_screen = (player.screen_x, player.screen_y)
            world_screen = world.get_screen(current_screen)
            game_map = world_screen.terrain
            footprints = player.get_footprints(current_screen)
            footprint_tile = world_screen.tiles.get("footprint")
            renderer.draw_map(
                game_map,
                player,
                enemies=world_screen.enemies,
                characters=world_screen.characters,
                hide_enemies=current_battle is not None,
                footprints=footprints,
                footprint_tile=footprint_tile,
            )

            talents_label = f"Золотые таланты: {player.talents}"

            if current_battle:
                renderer.draw_battle_ui(current_battle, talents_label)
            elif inventory_open:
                renderer.draw_inventory(player, talents_label)

            renderer.present()
            renderer.tick()

            event_handled = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit()
                if event.type != pygame.KEYDOWN:
                    continue

                key = event.key
                if key == pygame.K_ESCAPE:
                    raise SystemExit()

                if current_battle:
                    handled = False
                    if key in (pygame.K_1, pygame.K_KP1):
                        current_battle.attack_round()
                        handled = True
                    elif key in (pygame.K_2, pygame.K_KP2):
                        current_battle.run_away()
                        handled = True
                    elif key in (pygame.K_3, pygame.K_KP3):
                        current_battle.bribe()
                        handled = True

                    if handled and current_battle.finished:
                        if current_battle.result == "defeat":
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
                                player.set_position(
                                    prev_screen_x, prev_screen_y, prev_x, prev_y
                                )
                            elif current_battle.result == "bribe":
                                (
                                    prev_screen_x,
                                    prev_screen_y,
                                    prev_x,
                                    prev_y,
                                ) = current_battle.previous_state
                                player.set_position(
                                    prev_screen_x, prev_screen_y, prev_x, prev_y
                                )
                            else:
                                if current_battle.enemy in screen_enemies:
                                    screen_enemies.remove(current_battle.enemy)
                        current_battle = None
                    event_handled = True
                    break

                if inventory_open:
                    if key == pygame.K_i:
                        inventory_open = False
                        player.inventory.clear_message()
                    elif key == pygame.K_w:
                        player.inventory.move_cursor(0, -1)
                    elif key == pygame.K_s:
                        player.inventory.move_cursor(0, 1)
                    elif key == pygame.K_a:
                        player.inventory.move_cursor(-1, 0)
                    elif key == pygame.K_d:
                        player.inventory.move_cursor(1, 0)
                    elif key == pygame.K_e:
                        player.inventory.transfer_selected()
                    event_handled = True
                    break

                if key == pygame.K_i:
                    inventory_open = True
                    player.inventory.clear_message()
                    event_handled = True
                    break

                dx = 0
                dy = 0
                if key == pygame.K_w:
                    dy = -1
                elif key == pygame.K_s:
                    dy = 1
                elif key == pygame.K_a:
                    dx = -1
                elif key == pygame.K_d:
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
                event_handled = True
                break

            if event_handled:
                continue
    finally:
        renderer.close()


def main() -> None:
    if USE_PYGAME:
        run_pygame()
    else:
        run_ascii()


if __name__ == "__main__":
    main()
