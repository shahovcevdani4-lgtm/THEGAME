# Tile asset instructions

The pygame renderer expects a set of 16×16 PNG sprites to live in this directory.  Create the following files before running the game with `USE_PYGAME = True`:

| Filename        | Description | Notes |
|-----------------|-------------|-------|
| `grass.png`     | Base ground tile used for summer biome grass. | Fill the 16×16 image with a grass texture dominated by the RGB color (0, 120, 0) and optional darker speckles around (0, 60, 0).
| `tree.png`      | Blocking tree tile. | Draw a tree canopy that contrasts with the grass (suggested foliage RGB (100, 200, 100)) and make the trunk reach the bottom edge. The tile must still read clearly at 16×16.
| `stone.png`     | Impassable boulder tile. | Use a neutral gray palette around RGB (130, 130, 130). Consider a rounded silhouette with subtle highlights.
| `player.png`    | Player character sprite. | Center the character and keep background fully transparent. Use accent colors similar to RGB (240, 200, 80) for the outfit.
| `enemy.png`     | Generic hostile enemy sprite. | Draw the monster of your choice but keep a transparent outline. Fill the background with the aggressive maroon RGB (120, 0, 40) to match the in-game indicator.
| `warlock.png`   | Friendly warlock character. | Center a warlock silhouette tinted around RGB (180, 0, 200) on a dark backdrop (RGB ~ (20, 0, 40)).
| `footprint.png` | Temporary footprint left on winter biome tiles. | Design a small footprint mark using a pale blue RGB around (200, 200, 230) over a transparent background.

General requirements:

* Every sprite must be exactly **16×16 pixels**.
* Use a transparent background for everything except the maroon fill requested for aggressive enemies and the subtle dark aura behind the warlock.
* Save each image as a PNG with RGBA channels so transparency is preserved.
* Keep filenames lowercase to match the values referenced in `data/tiles.py`.
