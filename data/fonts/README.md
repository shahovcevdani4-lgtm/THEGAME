# Custom fonts

Place your `.ttf` or `.otf` font files in this directory to make them available to the game.

By default the game looks for a file named `main.ttf` (or `main.otf`) here and will fall back to the bundled `dejavu10x10_gs_tc.png` tileset if nothing is found.  You can also point the game at a specific font by setting the `ROGUELIKE_FONT` environment variable to the font file path.
