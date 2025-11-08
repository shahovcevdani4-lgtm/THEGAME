"""Sprite-based renderer built on pygame."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pygame

from engine.constants import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE


DEFAULT_TEXT_COLOR = (240, 240, 240)


def _slot_symbol(item) -> str:
    if item is None:
        return "·"
    symbol = getattr(item, "symbol", None)
    if callable(symbol):
        return symbol()
    if isinstance(item, str) and len(item) == 1:
        return item
    return str(item)[0]


def _is_two_handed_slot(inventory, slot_name: str) -> bool:
    item = inventory.active_slots.get(slot_name)
    if not item or not getattr(item, "two_handed", False):
        return False
    other = "weapon_off" if slot_name == "weapon_main" else "weapon_main"
    return inventory.active_slots.get(other) is item


class PygameRenderer:
    """Small helper responsible for loading tiles and drawing the UI."""

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.tile_size = TILE_SIZE
        self.width = SCREEN_WIDTH * self.tile_size
        self.height = SCREEN_HEIGHT * self.tile_size
        self._display_flags = pygame.RESIZABLE
        self.display = pygame.display.set_mode((self.width, self.height), self._display_flags)
        pygame.display.set_caption("Sprite Roguelike — прототип")
        self.canvas = pygame.Surface((self.width, self.height)).convert()
        self.window_size = self.display.get_size()
        self._saved_window_size = self.window_size
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 16)
        self.tiles = self._load_tiles(Path("data/tiles"))
        if not self.tiles:
            raise RuntimeError("Не удалось загрузить спрайты из data/tiles/.")
        self.default_key = next(iter(self.tiles))
        self.default_tile = self.tiles[self.default_key]
        self._flip_cache: dict[str, pygame.Surface] = {}

    def _load_tiles(self, directory: Path) -> dict[str, pygame.Surface]:
        tiles: dict[str, pygame.Surface] = {}
        if not directory.exists():
            return tiles
        for image_path in sorted(directory.glob("*.png")):
            surface = pygame.image.load(str(image_path)).convert_alpha()
            if surface.get_width() != self.tile_size or surface.get_height() != self.tile_size:
                surface = pygame.transform.smoothscale(
                    surface, (self.tile_size, self.tile_size)
                )
            tiles[image_path.stem] = surface
        return tiles

    def close(self) -> None:
        pygame.quit()

    def clear(self) -> None:
        self.canvas.fill((0, 0, 0))

    def present(self) -> None:
        if not self.display:
            return

        target_width, target_height = self.window_size
        if target_width <= 0 or target_height <= 0:
            return

        base_width, base_height = self.width, self.height
        scale = min(target_width / base_width, target_height / base_height)
        scaled_width = max(1, int(base_width * scale))
        scaled_height = max(1, int(base_height * scale))

        if scaled_width == base_width and scaled_height == base_height:
            scaled_surface = self.canvas
        else:
            scaled_surface = pygame.transform.smoothscale(
                self.canvas, (scaled_width, scaled_height)
            )

        self.display.fill((0, 0, 0))
        offset_x = (target_width - scaled_width) // 2
        offset_y = (target_height - scaled_height) // 2
        self.display.blit(scaled_surface, (offset_x, offset_y))
        pygame.display.flip()

    def set_window_size(self, size: tuple[int, int]) -> None:
        if self.fullscreen:
            return

        width = max(1, size[0])
        height = max(1, size[1])
        self.display = pygame.display.set_mode((width, height), self._display_flags)
        self.canvas = pygame.Surface((self.width, self.height)).convert()
        self.window_size = self.display.get_size()
        self._saved_window_size = self.window_size

    def toggle_fullscreen(self) -> None:
        if self.fullscreen:
            self.display = pygame.display.set_mode(
                self._saved_window_size, self._display_flags
            )
            self.fullscreen = False
        else:
            self._saved_window_size = self.window_size
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        self.window_size = self.display.get_size()
        self.canvas = pygame.Surface((self.width, self.height)).convert()

    def tick(self, fps: int = 60) -> None:
        self.clock.tick(fps)

    def _resolve_key(self, key: str | None, fallback: str | None = None) -> str:
        if key and key in self.tiles:
            return key
        if fallback and fallback in self.tiles:
            return fallback
        return self.default_key

    def _surface_for(self, key: str | None, fallback: str | None = None) -> pygame.Surface:
        resolved = self._resolve_key(key, fallback)
        return self.tiles.get(resolved, self.default_tile)

    def _flipped_surface(self, key: str, surface: pygame.Surface) -> pygame.Surface:
        cached = self._flip_cache.get(key)
        if cached is None:
            cached = pygame.transform.flip(surface, True, False)
            self._flip_cache[key] = cached
        return cached

    def draw_map(
        self,
        game_map,
        player,
        *,
        enemies=None,
        characters=None,
        hide_enemies: bool = False,
        footprints: Iterable[tuple[int, int]] | None = None,
        footprint_tile: dict | None = None,
    ) -> None:
        for y, row in enumerate(game_map):
            for x, tile in enumerate(row):
                tile_name = tile.get("tile_id") or tile.get("sprite") or tile.get("char")
                ground_name = tile.get("ground_tile")
                ground_key = self._resolve_key(ground_name, "grass")
                ground_surface = self.tiles.get(ground_key, self.default_tile)
                pos = (x * self.tile_size, y * self.tile_size)
                self.canvas.blit(ground_surface, pos)

                resolved_tile_key = self._resolve_key(tile_name, ground_key)
                if tile_name and resolved_tile_key != ground_key:
                    overlay_surface = self.tiles.get(resolved_tile_key, self.default_tile)
                    self.canvas.blit(overlay_surface, pos)

        if footprints and footprint_tile:
            footprint_name = footprint_tile.get("tile_id", "footprint")
            footprint_surface = self._surface_for(footprint_name, "footprint")
            for fx, fy in footprints:
                self.canvas.blit(
                    footprint_surface, (fx * self.tile_size, fy * self.tile_size)
                )

        if enemies and not hide_enemies:
            for enemy in enemies:
                if enemy and not enemy.defeated:
                    tile_name = getattr(enemy, "tile_key", None) or "enemy"
                    surface = self._surface_for(tile_name, "enemy")
                    self.canvas.blit(
                        surface, (enemy.x * self.tile_size, enemy.y * self.tile_size)
                    )

        if characters:
            for character in characters:
                tile_name = getattr(character, "tile_key", None) or "warlock"
                surface = self._surface_for(tile_name, "warlock")
                self.canvas.blit(
                    surface, (character.x * self.tile_size, character.y * self.tile_size)
                )

        player_key = self._resolve_key(getattr(player, "tile_key", None), "player")
        base_surface = self.tiles.get(player_key, self.default_tile)
        if getattr(player, "facing", 1) < 0:
            player_surface = self._flipped_surface(player_key, base_surface)
        else:
            player_surface = base_surface
        self.canvas.blit(player_surface, (player.x * self.tile_size, player.y * self.tile_size))

    def _draw_text_panel(
        self,
        lines: Sequence[str | tuple[str, tuple[int, int, int]]],
        *,
        anchor: str = "center",
    ) -> None:
        if not lines:
            return

        prepared: list[tuple[str, tuple[int, int, int]]] = []
        for entry in lines:
            if isinstance(entry, tuple):
                prepared.append(entry)
            else:
                prepared.append((entry, DEFAULT_TEXT_COLOR))

        max_width = max(self.font.size(text)[0] for text, _ in prepared)
        line_height = self.font.get_height()
        panel_width = max_width + 32
        panel_height = len(prepared) * line_height + 32
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((15, 15, 35, 235))
        pygame.draw.rect(panel, (90, 90, 140), panel.get_rect(), 2)

        for index, (text, color) in enumerate(prepared):
            rendered = self.font.render(text, True, color)
            panel.blit(rendered, (16, 16 + index * line_height))

        if anchor == "top-left":
            pos = (16, 16)
        elif anchor == "bottom-left":
            pos = (16, self.height - panel_height - 16)
        else:
            pos = ((self.width - panel_width) // 2, (self.height - panel_height) // 2)
        self.canvas.blit(panel, pos)

    def draw_battle_ui(self, battle, talents_label: str) -> None:
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

        self._draw_text_panel(lines, anchor="center")

    def draw_inventory(self, player, talents_label: str) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.canvas.blit(overlay, (0, 0))

        inventory = player.inventory
        slot_size = self.tile_size
        gap = 8
        line_height = self.small_font.get_height()

        panel_width = self.width - 80
        passive_rows = inventory.passive_rows
        panel_height = (
            24
            + line_height
            + slot_size
            + 12
            + line_height
            + passive_rows * (slot_size + 6)
            + 24
        )
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((25, 25, 55, 235))

        origin_x = (self.width - panel_width) // 2
        origin_y = max(16, (self.height - panel_height) // 2 - 32)

        label = self.font.render("Активные слоты:", True, (180, 200, 255))
        panel.blit(label, (24, 16))

        slots_y = 16 + line_height + 4
        for index, slot_name in enumerate(inventory.ACTIVE_SLOT_ORDER):
            slot_char = _slot_symbol(inventory.active_slots.get(slot_name))
            slot_x = 24 + index * (slot_size + gap)
            is_selected = index == inventory.cursor_index
            is_two_handed = _is_two_handed_slot(inventory, slot_name)
            color = (90, 70, 120) if is_selected else (55, 55, 80)
            if is_two_handed and not is_selected:
                color = (70, 50, 90)
            rect = pygame.Rect(slot_x, slots_y, slot_size, slot_size)
            pygame.draw.rect(panel, color, rect)
            pygame.draw.rect(panel, (20, 20, 30), rect, 2)
            glyph = self.font.render(slot_char, True, (230, 230, 230))
            glyph_rect = glyph.get_rect(center=rect.center)
            panel.blit(glyph, glyph_rect)

        passive_label_y = slots_y + slot_size + 12
        passive_label = self.font.render("Пассивные слоты:", True, (180, 200, 255))
        panel.blit(passive_label, (24, passive_label_y))

        grid_start_y = passive_label_y + line_height + 2
        total_active = len(inventory.ACTIVE_SLOT_ORDER)
        for row in range(passive_rows):
            for col in range(inventory.columns):
                slot_index = total_active + row * inventory.columns + col
                slot_char = _slot_symbol(inventory.slot_at(slot_index))
                slot_x = 24 + col * (slot_size + gap)
                slot_y = grid_start_y + row * (slot_size + 6)
                is_selected = slot_index == inventory.cursor_index
                color = (90, 70, 120) if is_selected else (40, 40, 60)
                rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
                pygame.draw.rect(panel, color, rect)
                pygame.draw.rect(panel, (20, 20, 30), rect, 2)
                glyph = self.font.render(slot_char, True, (220, 220, 220))
                glyph_rect = glyph.get_rect(center=rect.center)
                panel.blit(glyph, glyph_rect)

        self.canvas.blit(panel, (origin_x, origin_y))

        context_height = 8 + 7 * (line_height + 2)
        context = pygame.Surface((self.width, context_height), pygame.SRCALPHA)
        context.fill((15, 15, 35, 235))

        lines: list[tuple[str, tuple[int, int, int]]] = []
        lines.append((f"Имя: {player.name}", (245, 245, 245)))
        lines.append((f"Класс: {player.character_class}", (200, 200, 255)))
        stats_line = f"STR {player.strength}  AGI {player.agility}  INT {player.intelligence}"
        lines.append((stats_line, (200, 255, 200)))
        lines.append((talents_label, (255, 215, 0)))
        lines.append((f"Слот: {inventory.slot_label(inventory.cursor_index)}", (220, 220, 220)))

        selected = inventory.selected_item()
        if selected is not None:
            descriptor = selected.slot_type
            if descriptor == "upper":
                descriptor = "верхняя одежда"
            elif descriptor == "boots":
                descriptor = "обувь"
            elif descriptor == "weapon":
                descriptor = "оружие"
            item_line = f"Выбрано: {selected.name} ({descriptor})"
            if getattr(selected, "two_handed", False):
                item_line += " — двуручное"
            lines.append((item_line, (210, 230, 255)))

        if inventory.last_message:
            lines.append((inventory.last_message, (255, 230, 120)))

        lines.append(("Управление: WASD — выбор, E — перенос, I — закрыть", (180, 180, 200)))

        for index, (text, color) in enumerate(lines[:7]):
            rendered = self.small_font.render(text, True, color)
            context.blit(rendered, (16, 8 + index * (line_height + 2)))

        self.canvas.blit(context, (0, self.height - context_height))

    def show_class_menu(self, classes) -> str:
        options = [
            "Выбери класс:",
            "",
        ]
        for i, (cid, cls) in enumerate(classes.items(), start=1):
            options.append(
                f"[{i}] {cls['name']} (STR {cls['str']} / AGI {cls['agi']} / INT {cls['int']})"
            )

        while True:
            self.clear()
            self._draw_text_panel(options, anchor="center")
            self.present()
            self.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    raise SystemExit()
                if event.type in {pygame.VIDEORESIZE, pygame.WINDOWRESIZED}:
                    self.set_window_size((event.w, event.h))
                    continue
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if event.key in (pygame.K_1, pygame.K_KP1):
                    return list(classes.keys())[0]
                if event.key in (pygame.K_2, pygame.K_KP2) and len(classes) > 1:
                    return list(classes.keys())[1]

