# main.py
from __future__ import annotations

from collections.abc import Callable
import time

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


def _active_direction(order: list, mapping: dict) -> tuple[int, int] | None:
    for key in reversed(order):
        if key in mapping:
            return mapping[key]
    return None


def _status_label(player: Player) -> str:
    return f"Золотые таланты: {player.talents}"


def _finalize_battle(
    battle: Battle | None,
    player: Player,
    world,
    *,
    on_defeat: Callable[[], None] | None = None,
) -> Battle | None:
    if not battle or not battle.finished:
        return battle

    if battle.result == "defeat":
        if on_defeat is not None:
            on_defeat()
        raise SystemExit("Вы пали в бою.")

    enemy_screen = (battle.enemy.screen_x, battle.enemy.screen_y)
    screen_enemies = world.enemies_at(enemy_screen)

    if battle.result == "run":
        battle.enemy.hp = battle.enemy.max_hp
        prev_screen_x, prev_screen_y, prev_x, prev_y = battle.previous_state
        player.set_position(prev_screen_x, prev_screen_y, prev_x, prev_y)
    elif battle.result == "bribe":
        prev_screen_x, prev_screen_y, prev_x, prev_y = battle.previous_state
        player.set_position(prev_screen_x, prev_screen_y, prev_x, prev_y)
    elif battle.result == "victory":
        if battle.enemy in screen_enemies:
            screen_enemies.remove(battle.enemy)

    return None


def attempt_player_move(player: Player, world, dx: int, dy: int) -> tuple[bool, Battle | None]:
    if dx == 0 and dy == 0:
        return False, None

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
        return False, None

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
        return False, None

    target_screen = (player.screen_x + screen_dx, player.screen_y + screen_dy)
    target_map = (
        current_map if target_screen == previous_screen_coords else world.map_at(target_screen)
    )

    if not target_map[new_y][new_x]["walkable"]:
        return False, None

    if dx:
        player.update_facing(dx)

    if target_screen != previous_screen_coords:
        player.set_position(target_screen[0], target_screen[1], new_x, new_y)
    else:
        player.x = new_x
        player.y = new_y

    if world.biome_at(previous_screen_coords) == "winter":
        player.leave_footprint(previous_screen_coords, previous_tile)

    current_screen_enemies = world.enemies_at((player.screen_x, player.screen_y))
    for enemy in current_screen_enemies:
        if not enemy.defeated and player.x == enemy.x and player.y == enemy.y:
            return True, Battle(player, enemy, previous_state)

    return True, None


def run_ascii() -> None:
    tileset, used_font = load_preferred_tileset()
    if used_font is not None:
        print(f"Используем шрифт: {used_font}")
    else:
        print(
            "Не удалось найти подходящий шрифт в data/fonts/ — будет использован стандартный tileset."
        )

    movement_keys = {
        KeySym.W: (0, -1),
        KeySym.w: (0, -1),
        KeySym.S: (0, 1),
        KeySym.s: (0, 1),
        KeySym.A: (-1, 0),
        KeySym.a: (-1, 0),
        KeySym.D: (1, 0),
        KeySym.d: (1, 0),
    }

    held_directions: dict[KeySym, tuple[int, int]] = {}
    held_order: list[KeySym] = []
    movement_progress = 0.0
    last_time = time.perf_counter()

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
            now = time.perf_counter()
            delta = now - last_time
            last_time = now

            world.advance_time(delta)

            for raw_event in tcod.event.get():
                event = context.convert_event(raw_event)
                if event.type == "QUIT":
                    raise SystemExit()

                if event.type == "KEYUP":
                    if event.sym in movement_keys:
                        held_directions.pop(event.sym, None)
                        if event.sym in held_order:
                            held_order[:] = [key for key in held_order if key != event.sym]
                    continue

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

                    if handled:
                        current_battle = _finalize_battle(
                            current_battle,
                            player,
                            world,
                            on_defeat=lambda: context.present(console),
                        )
                    continue

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
                    continue

                if event.sym in (KeySym.I, KeySym.i):
                    inventory_open = True
                    player.inventory.clear_message()
                    held_directions.clear()
                    held_order.clear()
                    movement_progress = 0.0
                    continue

                if event.sym in movement_keys:
                    if event.sym not in held_directions:
                        held_directions[event.sym] = movement_keys[event.sym]
                        held_order.append(event.sym)
                    interval = player.movement_interval
                    if interval > 0:
                        movement_progress = max(movement_progress, interval)
                    continue

            if not current_battle and not inventory_open:
                direction = _active_direction(held_order, held_directions)
                if direction:
                    movement_progress += delta
                    interval = player.movement_interval
                    if interval > 0:
                        while movement_progress >= interval:
                            moved, new_battle = attempt_player_move(
                                player, world, direction[0], direction[1]
                            )
                            if not moved:
                                movement_progress = min(movement_progress, interval)
                                break
                            movement_progress -= interval
                            if new_battle is not None:
                                current_battle = new_battle
                                inventory_open = False
                                held_directions.clear()
                                held_order.clear()
                                movement_progress = 0.0
                                break
                else:
                    movement_progress = 0.0
            else:
                movement_progress = 0.0

            console.clear()
            viewport = world.build_viewport(player)
            draw_map(
                console,
                viewport.tiles,
                player,
                viewport.player_position,
                enemies=viewport.enemies,
                characters=viewport.characters,
                hide_enemies=current_battle is not None,
                footprints=viewport.footprints,
            )

            status_label = _status_label(player)

            if current_battle:
                draw_battle_ui(console, current_battle, status_label)
            elif inventory_open:
                draw_inventory(console, player, status_label)

            context.present(console)


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

        movement_keys = {
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0),
        }
        held_directions: dict[int, tuple[int, int]] = {}
        held_order: list[int] = []
        movement_progress = 0.0

        while True:
            delta = renderer.tick()
            world.advance_time(delta)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit()
                if event.type in {pygame.VIDEORESIZE, pygame.WINDOWRESIZED}:
                    renderer.set_window_size((event.w, event.h))
                    continue
                if event.type == pygame.KEYUP:
                    if event.key in movement_keys:
                        held_directions.pop(event.key, None)
                        if event.key in held_order:
                            held_order[:] = [key for key in held_order if key != event.key]
                    continue
                if event.type != pygame.KEYDOWN:
                    continue

                key = event.key
                if key == pygame.K_F11:
                    renderer.toggle_fullscreen()
                    continue
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

                    if handled:
                        current_battle = _finalize_battle(current_battle, player, world)
                    continue

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
                    continue

                if key == pygame.K_i:
                    inventory_open = True
                    player.inventory.clear_message()
                    held_directions.clear()
                    held_order.clear()
                    movement_progress = 0.0
                    continue

                if key in movement_keys:
                    if key not in held_directions:
                        held_directions[key] = movement_keys[key]
                        held_order.append(key)
                    interval = player.movement_interval
                    if interval > 0:
                        movement_progress = max(movement_progress, interval)
                    continue

            if not current_battle and not inventory_open:
                direction = _active_direction(held_order, held_directions)
                if direction:
                    movement_progress += delta
                    interval = player.movement_interval
                    if interval > 0:
                        while movement_progress >= interval:
                            moved, new_battle = attempt_player_move(
                                player, world, direction[0], direction[1]
                            )
                            if not moved:
                                movement_progress = min(movement_progress, interval)
                                break
                            movement_progress -= interval
                            if new_battle is not None:
                                current_battle = new_battle
                                inventory_open = False
                                held_directions.clear()
                                held_order.clear()
                                movement_progress = 0.0
                                break
                else:
                    movement_progress = 0.0
            else:
                movement_progress = 0.0

            renderer.clear()
            viewport = world.build_viewport(player)
            renderer.draw_map(
                viewport.tiles,
                player,
                viewport.player_position,
                enemies=viewport.enemies,
                characters=viewport.characters,
                hide_enemies=current_battle is not None,
                footprints=viewport.footprints,
            )

            status_label = _status_label(player)

            if current_battle:
                renderer.draw_battle_ui(current_battle, status_label)
            elif inventory_open:
                renderer.draw_inventory(player, status_label)

            renderer.present()
    finally:
        renderer.close()


def main() -> None:
    if USE_PYGAME:
        run_pygame()
    else:
        run_ascii()


if __name__ == "__main__":
    main()
