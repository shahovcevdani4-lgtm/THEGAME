"""Asset loading helpers for fonts and tilesets."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import tcod

FONT_ENV_VAR = "ROGUELIKE_FONT"
FONT_PRIORITY = (
    Path("data/fonts/main.ttf"),
    Path("data/fonts/main.otf"),
    Path("dejavu10x10_gs_tc.png"),
)


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
