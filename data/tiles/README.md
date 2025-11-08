# Tile asset instructions

The pygame renderer expects a set of 16×16 PNG sprites to live in this directory. Create the following files before running the
game with `USE_PYGAME = True`:

| Filename | Description | Notes |
|----------|-------------|-------|
| `summer_ground.png` | Ground tile for the summer biome. | Fill the 16×16 image with a lively grass texture dominated by RGB colours around (20, 150, 40) with darker speckles close to (5, 70, 15). |
| `summer_tree.png` | Blocking summer tree. | Draw a lush tree canopy that stands out from the grass (foliage RGB around (90, 200, 90)) and ensure the trunk touches the bottom edge. |
| `summer_boulder.png` | Summer biome boulder. | Use a neutral gray palette around RGB (130, 130, 130) with subtle highlights so it looks distinct from the grass. |
| `winter_ground.png` | Ground tile for the winter biome. | Create a snow texture using pale blues around RGB (230, 230, 255) with a slightly darker base near (210, 210, 235). |
| `winter_tree.png` | Snow-covered tree. | Paint a stylised conifer using cool blues (~(30, 90, 160)) that contrasts the snow background. |
| `winter_snowdrift.png` | Walkable snow drift. | Draw a small mound of snow with highlights around RGB (200, 200, 230) over the same snowy base colour. |
| `drought_ground.png` | Ground tile for the drought biome. | Use a sandy palette with hues near RGB (215, 180, 90) and shading around (170, 130, 60). |
| `drought_cactus.png` | Cactus obstacle. | Draw a simple cactus silhouette using greens close to RGB (60, 140, 70) over the sandy backdrop. |
| `drought_dead_tree.png` | Withered tree obstacle. | Sketch a bare tree using warm browns (~(150, 90, 40)) that contrasts the sand. |
| `player.png` | Player character sprite. | Center the character and keep background fully transparent. Use accent colors similar to RGB (240, 200, 80) for the outfit. |
| `enemy.png` | Generic hostile enemy sprite. | Draw the monster of your choice but keep a transparent outline. Fill the background with the aggressive maroon RGB (120, 0, 40) to match the in-game indicator. |
| `warlock.png` | Friendly warlock character. | Center a warlock silhouette tinted around RGB (180, 0, 200) on a dark backdrop (RGB ~ (20, 0, 40)). |
| `footprint.png` | Temporary footprint left on winter biome tiles. | Design a small footprint mark using a pale blue RGB around (200, 200, 230) over a transparent background. |

General requirements:

* Every sprite must be exactly **16×16 pixels**.
* Use a transparent background for everything except the maroon fill requested for aggressive enemies and the subtle dark aura behind the warlock.
* Save each image as a PNG with RGBA channels so transparency is preserved.
* Keep filenames lowercase to match the values referenced in `data/tiles.py`.
