"""Asset loading helpers for fonts, tilesets, and optional sprites."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import tcod
from tcod import image as tcod_image

FONT_ENV_VAR = "ROGUELIKE_FONT"
FONT_PRIORITY = (
    Path("data/fonts/main.ttf"),
    Path("data/fonts/main.otf"),
    Path("dejavu10x10_gs_tc.png"),
)


@dataclass
class Sprite:
    """Simple sprite wrapper with graceful ASCII fallback rendering."""

    path: Path
    fallback_char: str
    fallback_fg: tuple[int, int, int]
    fallback_bg: tuple[int, int, int] = (0, 0, 0)
    _image: "tcod.image.Image | None" = None

    def ensure_loaded(self) -> None:
        """Attempt to load the sprite image if it has not been loaded yet."""

        if self._image is not None:
            return
        try:
            self._image = tcod_image.load(str(self.path))
        except Exception as exc:  # pragma: no cover - runtime best-effort logging
            print(f"Не удалось загрузить спрайт {self.path}: {exc}")
            self._image = None

    def draw(self, console: "tcod.console.Console", x: int, y: int) -> None:
        """Draw the sprite or fall back to ASCII if blitting fails."""

        self.ensure_loaded()
        if self._image is not None:
            try:
                # Attempt to blit the image directly; fall back to ASCII if it fails.
                self._image.blit(
                    console, x, y, 1.0, 1.0, 0.0  # type: ignore[arg-type]
                )
                return
            except Exception as exc:  # pragma: no cover - runtime logging only
                print(f"Не удалось отрисовать спрайт {self.path}: {exc}")
                self._image = None

        console.print(x, y, self.fallback_char, fg=self.fallback_fg, bg=self.fallback_bg)


def load_sprite(
    path: "str | os.PathLike[str]",
    fallback_char: str,
    fallback_fg: tuple[int, int, int],
    fallback_bg: tuple[int, int, int] = (0, 0, 0),
) -> Sprite:
    """Create a sprite description that falls back to ASCII when unavailable."""

    sprite_path = Path(path)
    sprite = Sprite(
        path=sprite_path,
        fallback_char=fallback_char,
        fallback_fg=fallback_fg,
        fallback_bg=fallback_bg,
    )
    if sprite_path.exists():
        sprite.ensure_loaded()
    return sprite


def load_tileset(font_file: "str | os.PathLike[str]") -> "tcod.tileset.Tileset | None":
    """Load a font or tileset, supporting PNG and TTF/OTF formats."""

    path = Path(font_file)
    if not path.exists():
        return None

    suffix = path.suffix.lower()
    try:
        if suffix == ".png":
            return tcod.tileset.load_tilesheet(
                str(path), 32, 8, tcod.tileset.CHARMAP_TCOD
            )
        if suffix in {".ttf", ".otf"}:
            return tcod.tileset.load_truetype_font(
                str(path), 32, 8, charmap=tcod.tileset.CHARMAP_TCOD
            )
    except Exception as exc:  # pragma: no cover - we only log failures in runtime
        print(f"Не удалось загрузить шрифт {path}: {exc}")
    return None


def iter_font_candidates() -> Iterator[Path]:
    """Yield font paths in priority order, honouring the environment override."""

    override = os.environ.get(FONT_ENV_VAR)
    if override:
        yield Path(override)
    for candidate in FONT_PRIORITY:
        yield Path(candidate)


def load_preferred_tileset() -> tuple["tcod.tileset.Tileset | None", Path | None]:
    """Pick the first available tileset according to priority."""

    for candidate in iter_font_candidates():
        tileset = load_tileset(candidate)
        if tileset is not None:
            return tileset, candidate
    return None, None
