from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


TimerMode = Literal["x1", "x10", "instant"]


class Monster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    species: str
    level: int = Field(default=1, ge=1, le=20)
    island: str = "Plant Island"


class PlayerState(BaseModel):
    name: str = "Test"
    coins: int = Field(default=999_999, ge=0)
    diamonds: int = Field(default=9_999, ge=0)
    food: int = Field(default=999_999, ge=0)
    timer_mode: TimerMode = "instant"
    active_island: str = "Plant Island"
    monsters: list[Monster] = Field(
        default_factory=lambda: [
            Monster(species="Mammott", level=20),
            Monster(species="Noggin", level=20),
        ]
    )


class CurrencyPatch(BaseModel):
    coins: int | None = Field(default=None, ge=0)
    diamonds: int | None = Field(default=None, ge=0)
    food: int | None = Field(default=None, ge=0)


class MonsterCreate(BaseModel):
    species: str = Field(min_length=1, max_length=80)
    level: int = Field(default=1, ge=1, le=20)
    island: str = Field(default="Plant Island", min_length=1, max_length=80)


class MonsterLevelPatch(BaseModel):
    level: int = Field(ge=1, le=20)


class TimerPatch(BaseModel):
    mode: TimerMode
