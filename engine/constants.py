"""Centralized configuration constants for map and world dimensions."""

# Размер видимой области в блоках (ширина × высота).
SCREEN_WIDTH = 85
SCREEN_HEIGHT = 50

# Размер одного "экрана" карты. Его ширина совпадает с шириной экрана,
# но камера может свободно перемещаться между соседними экранами.
MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT

# Базовый размер тайла. Pygame-рендерер увеличивает его при отрисовке,
# чтобы камера была визуально ближе к игроку.
TILE_SIZE = 16

# Глобальная карта состоит из 50×50 экранов.
WORLD_COLUMNS = 50
WORLD_ROWS = 50
TOTAL_SCREENS = WORLD_COLUMNS * WORLD_ROWS
assert TOTAL_SCREENS == 2500

# Параметры передвижения.
BASE_MOVEMENT_SPEED = 3.0  # клеток в секунду
AGILITY_SPEED_BONUS = 0.35  # дополнительная скорость за каждую единицу ловкости
