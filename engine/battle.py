# engine/battle.py
import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.assets import Sprite


@dataclass
class Enemy:
    name: str
    char: str
    fg: Tuple[int, int, int]
    bg: Tuple[int, int, int]
    max_hp: int
    attack_min: int
    attack_max: int
    reward_talents: int
    stats: dict
    x: int
    y: int
    screen_x: int
    screen_y: int
    hp: Optional[int] = None
    defeated: bool = False
    sprite: "Sprite | None" = None

    def __post_init__(self):
        self.hp = self.max_hp

    @property
    def strength(self) -> int:
        return self.stats.get("str", 0)

    @property
    def dexterity(self) -> int:
        return self.stats.get("dex", 0)

    @property
    def intelligence(self) -> int:
        return self.stats.get("int", 0)

    def average_power(self) -> float:
        return (self.strength + self.dexterity + self.intelligence) / 3

    def attack_damage(self) -> int:
        return random.randint(self.attack_min, self.attack_max)


class Battle:
    def __init__(
        self,
        player,
        enemy: Enemy,
        previous_state: Tuple[int, int, int, int],
    ):
        self.player = player
        self.enemy = enemy
        self.previous_state = previous_state
        self.log: List[str] = [f"Вы вступили в бой с {enemy.name}!"]
        self.finished = False
        self.result: Optional[str] = None
        self._run_attempt_locked = False

    def _append_log(self, message: str) -> None:
        self.log.append(message)
        self.log = self.log[-6:]

    def can_run(self) -> bool:
        threshold = (self.enemy.dexterity + self.enemy.intelligence) / 2
        return (
            self.player.dexterity >= threshold
            or self.player.intelligence >= threshold
        )

    def run_away(self) -> bool:
        if self._run_attempt_locked:
            self._append_log("Вы уже пытались бежать — теперь только бой!")
            return False

        if not self.can_run():
            self._append_log("Слишком страшно бежать!")
            return False

        bonus = self.player.dexterity // 3
        roll = random.randint(1, 12)
        total = roll + bonus
        if total >= 6:
            self._append_log(
                f"Побег успешен! (бросок {roll} + бонус {bonus} = {total})"
            )
            self.finished = True
            self.result = "run"
            return True

        self._append_log(
            f"Побег не удался (бросок {roll} + бонус {bonus} = {total})"
        )
        self._run_attempt_locked = True
        self.enemy_attack()
        return False

    def bribe_cost(self, enemy_count: int = 1) -> int:
        base = self.player.talents * 0.15
        scaled = base * (1.5 ** enemy_count)
        cost = 10 + max(base, scaled)
        return max(0, math.ceil(cost))

    def bribe(self, enemy_count: int = 1) -> bool:
        cost = self.bribe_cost(enemy_count)
        if self.player.talents < cost:
            self._append_log("Недостаточно талантов для откупа!")
            return False

        self.player.talents = max(0, self.player.talents - cost)
        self._append_log(
            f"Вы заплатили {cost} талантов. Противник принимает золото, но остаётся поблизости."
        )
        self.enemy.defeated = False
        self.enemy.hp = self.enemy.max_hp
        self.finished = True
        self.result = "bribe"
        return True

    def player_attack(self) -> None:
        damage = self.player.attack_damage()
        self.enemy.hp = max(0, self.enemy.hp - damage)
        self._append_log(f"Вы наносите {damage} урона.")
        if self.enemy.hp <= 0:
            self._append_log(f"{self.enemy.name} повержен!")
            self.finished = True
            self.result = "victory"

    def enemy_attack(self) -> None:
        if self.enemy.hp <= 0:
            return
        damage = self.enemy.attack_damage()
        self.player.hp = max(0, self.player.hp - damage)
        self._append_log(f"{self.enemy.name} кусает на {damage} урона!")
        if self.player.hp <= 0:
            self._append_log("Вы погибли...")
            self.finished = True
            self.result = "defeat"

    def attack_round(self) -> None:
        if self.finished:
            return

        turn_order = [
            (self.player.average_power(), "player"),
            (self.enemy.average_power(), "enemy"),
        ]
        turn_order.sort(key=lambda item: item[0], reverse=True)

        for _, actor in turn_order:
            if self.finished:
                break
            if actor == "player":
                self.player_attack()
            else:
                self.enemy_attack()

        if self.result == "victory":
            self.enemy.defeated = True
            self.player.talents += self.enemy.reward_talents
            self._append_log(
                f"Вы получили {self.enemy.reward_talents} талант(ов)."
            )
