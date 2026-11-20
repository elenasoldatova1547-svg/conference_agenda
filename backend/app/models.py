"""Модели данных (Pydantic v2) для «Маршрут для участника конференции».

Соответствуют разделу 3 ТЗ (сущности + ERD) и OpenAPI-схемам из раздела 4.3.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enum'ы (справочники)                                                         #
# --------------------------------------------------------------------------- #
class Track(str, Enum):
    """7 фиксированных тем конференции (BR-02)."""

    processes = "processes"
    tools = "tools"
    career = "career"
    ui_ux = "ui_ux"
    clients_cases = "clients_cases"
    architecture = "architecture"
    data = "data"


# Отображение кода темы в человекочитаемое название (используется справочником
# /api/tracks и fallback-текстами объяснений).
TRACK_LABELS: dict[Track, str] = {
    Track.processes: "Процессы",
    Track.tools: "Инструменты",
    Track.career: "Карьера и развитие",
    Track.ui_ux: "UI/UX",
    Track.clients_cases: "Клиенты и кейсы",
    Track.architecture: "Архитектура, методологии",
    Track.data: "Работа с данными",
}


class TalkFormat(str, Enum):
    talk = "talk"
    workshop = "workshop"
    roundtable = "roundtable"


class Language(str, Enum):
    ru = "ru"
    en = "en"


class Level(str, Enum):
    junior = "junior"
    middle = "middle"
    senior = "senior"
    lead = "lead"


class LanguagePref(str, Enum):
    ru = "ru"
    en = "en"
    any = "any"


class Walking(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SlotType(str, Enum):
    talk = "talk"
    lunch = "lunch"
    networking = "networking"


# --------------------------------------------------------------------------- #
# Справочники / статические сущности                                           #
# --------------------------------------------------------------------------- #
class TrackInfo(BaseModel):
    """Элемент справочника тем для /api/tracks."""

    code: Track
    label: str


class ConferenceDay(BaseModel):
    """День конференции с окном обеда (BR-05 — ровно 1 час)."""

    day: int = Field(..., ge=1, le=2)
    lunch_start: str = Field(..., examples=["13:00"])
    lunch_end: str = Field(..., examples=["14:00"])


class Talk(BaseModel):
    """Доклад / активность (раздел 3.1 ТЗ)."""

    id: str = Field(..., examples=["talk_101"])
    title: str
    speaker: str
    company: str = ""
    track: Track
    day: int = Field(..., ge=1, le=2)
    start: str = Field(..., examples=["10:00"])
    end: str = Field(..., examples=["10:40"])
    room: str = Field(..., examples=["Секция A"])
    format: TalkFormat
    language: Language = Language.ru
    level: Level = Level.middle
    tags: list[str] = Field(default_factory=list)
    description_short: str = ""


class Program(BaseModel):
    """Ответ /api/program: полное расписание на 2 дня."""

    days: list[ConferenceDay]
    talks: list[Talk]


# --------------------------------------------------------------------------- #
# Вход от участника                                                            #
# --------------------------------------------------------------------------- #
class UserGoals(BaseModel):
    """Цели участника (раздел 3.1 ТЗ)."""

    priorities: list[Track] = Field(..., min_length=1)
    experience_level: Level
    wants_workshops: bool = False
    max_walking: Walking = Walking.medium
    must_attend: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    language_pref: LanguagePref = LanguagePref.any


# --------------------------------------------------------------------------- #
# Результат                                                                    #
# --------------------------------------------------------------------------- #
class DaySlot(BaseModel):
    """Слот маршрута (раздел 3.1 ТЗ)."""

    type: SlotType
    time: str = Field(..., examples=["10:00–10:40"])
    talk: Optional[Talk] = None
    reason: str = ""
    conflicts: list[str] = Field(default_factory=list)


class RouteDay(BaseModel):
    day: int
    slots: list[DaySlot]


class Route(BaseModel):
    """Результат построения маршрута."""

    route_id: str = Field(..., examples=["b1e2c3d4-..."])
    goals: UserGoals
    days: list[RouteDay]
    overall_strategy: str
