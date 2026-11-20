"""Хранилище данных: загрузка program.json и in-memory кэш маршрутов.

Реального API AnalystDays нет (раздел 1 ТЗ) — расписание читается из мок-файла
backend/app/data/program.json один раз при старте сервиса.
"""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path

from .models import ConferenceDay, Program, Route, Talk

DATA_FILE = Path(__file__).resolve().parent / "data" / "program.json"


class ProgramStore:
    """Ленивое хранилище расписания + сохранённых маршрутов."""

    def __init__(self) -> None:
        self._loaded = False
        self._lock = threading.Lock()
        self._talks: dict[str, Talk] = {}
        self._talks_by_day: dict[int, list[Talk]] = {}
        self._days: list[ConferenceDay] = []
        self._routes: dict[str, Route] = {}

    # ----- загрузка ------------------------------------------------------- #
    def _load(self) -> None:
        if self._loaded:
            return
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        program = Program.model_validate(raw)
        self._days = program.days
        self._talks = {t.id: t for t in program.talks}
        by_day: dict[int, list[Talk]] = {}
        for t in program.talks:
            by_day.setdefault(t.day, []).append(t)
        for day in by_day:
            by_day[day].sort(key=lambda t: (t.start, t.room))
        self._talks_by_day = by_day
        self._loaded = True

    # ----- чтение --------------------------------------------------------- #
    def get_program(self) -> Program:
        with self._lock:
            self._load()
            return Program(days=self._days, talks=list(self._talks.values()))

    def get_days(self) -> list[ConferenceDay]:
        with self._lock:
            self._load()
            return list(self._days)

    def get_talk(self, talk_id: str) -> Talk | None:
        with self._lock:
            self._load()
            return self._talks.get(talk_id)

    def talks_for_day(self, day: int) -> list[Talk]:
        with self._lock:
            self._load()
            return list(self._talks_by_day.get(day, []))

    def all_talk_ids(self) -> set[str]:
        with self._lock:
            self._load()
            return set(self._talks.keys())

    # ----- маршруты ------------------------------------------------------- #
    def save_route(self, route: Route) -> None:
        with self._lock:
            self._routes[route.route_id] = route

    def get_route(self, route_id: str) -> Route | None:
        with self._lock:
            return self._routes.get(route_id)

    @staticmethod
    def new_route_id() -> str:
        return str(uuid.uuid4())


# Едиственный экземпляр для всего процесса.
store = ProgramStore()
