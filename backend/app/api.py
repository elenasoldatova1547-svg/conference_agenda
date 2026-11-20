"""REST-эндпоинты /api/* (раздел 4 ТЗ)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import llm
from .engine import build_route
from .models import TRACK_LABELS, Program, Route, Talk, TrackInfo, UserGoals
from .store import store

router = APIRouter(prefix="/api", tags=["route-builder"])


@router.get("/program", response_model=Program, summary="Полное расписание на 2 дня")
def get_program() -> Program:
    return store.get_program()


@router.get("/tracks", response_model=list[TrackInfo], summary="Справочник 7 тем")
def get_tracks() -> list[TrackInfo]:
    return [TrackInfo(code=code, label=label) for code, label in TRACK_LABELS.items()]


@router.get("/talk/{talk_id}", response_model=Talk, summary="Детали доклада по ID")
def get_talk(talk_id: str) -> Talk:
    talk = store.get_talk(talk_id)
    if talk is None:
        raise HTTPException(status_code=404, detail=f"Доклад {talk_id} не найден")
    return talk


@router.post("/route", response_model=Route, summary="Построить маршрут по целям участника")
def post_route(goals: UserGoals) -> Route:
    # Валидация must_attend / avoid: несуществующий ID → 422 (раздел 4.2 ТЗ)
    known = store.all_talk_ids()
    unknown_must = [t for t in goals.must_attend if t not in known]
    if unknown_must:
        raise HTTPException(
            status_code=422,
            detail=f"Несуществующий must_attend: {', '.join(unknown_must)}",
        )
    unknown_avoid = [t for t in goals.avoid if t not in known]
    if unknown_avoid:
        raise HTTPException(
            status_code=422,
            detail=f"Несуществующий avoid: {', '.join(unknown_avoid)}",
        )

    route = build_route(goals)
    route = llm.enrich_route(route, goals)  # no-op, если LLM выключен
    return route


@router.get("/route/{route_id}", response_model=Route, summary="Получить сохранённый маршрут")
def get_route(route_id: str) -> Route:
    route = store.get_route(route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Маршрут не найден")
    return route
