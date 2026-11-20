"""Движок построения маршрута.

Алгоритм (согласно BPMN-диаграмме ТЗ):
  1. Скоринг докладов: +3 главный трек, +1 второстепенный, +2 воркшоп,
     +100 must_attend, −100 avoid, бонус совпадения уровня, штраф за язык.
  2. Фиксация must_attend.
  3. Блокировка обеда (lunch_start–lunch_end, score = −∞).
  4. Жадный выбор по слотам с учётом walking-штрафа.
  5. Fallback-объяснения (LLM опционален, раздел 4.3 ТЗ).
  6. Вставка lunch-слотов.
  7. Формирование Route {route_id, days, overall_strategy}.
"""

from __future__ import annotations

import math
from typing import Optional

from .models import (
    ConferenceDay,
    DaySlot,
    Level,
    LanguagePref,
    Route,
    RouteDay,
    SlotType,
    Talk,
    TalkFormat,
    Track,
    TrackInfo,
    UserGoals,
    TRACK_LABELS,
)
from .store import store

# --------------------------------------------------------------------------- #
# Вспомогательные функции                                                    #
# --------------------------------------------------------------------------- #
def _time_to_min(t: str) -> int:
    """Парсит «HH:MM» → минуты от полуночи."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _overlaps(start: str, end: str, s2: str, e2: str) -> bool:
    """True, если интервалы [start,end) и [s2,e2) пересекаются."""
    a, b = _time_to_min(start), _time_to_min(end)
    c, d = _time_to_min(s2), _time_to_min(e2)
    return a < d and c < b


def _level_distance(user: Level, talk: Level) -> int:
    order = [Level.junior, Level.middle, Level.senior, Level.lead]
    iu = order.index(user) if user in order else 1
    it = order.index(talk) if talk in order else 1
    return abs(iu - it)


def _walking_penalty(walking: str) -> float:
    """Штраф за смену зала: low=−4, medium=−1.5, high=−0.5.

    Держим штраф мягким, чтобы приоритет темы (+3/+1) оставался главным
    фактором выбора, а логистика — вторичным.
    """
    return {"low": -4.0, "medium": -1.5, "high": -0.5}.get(walking, -1.5)


# --------------------------------------------------------------------------- #
# Скоринг                                                                     #
# --------------------------------------------------------------------------- #
def _score_talk(talk: Talk, goals: UserGoals, prev_room: Optional[str]) -> float:
    """Возвращает скоринг доклада. Отрицательный → не выбирать."""
    score = 0.0

    # Трек: главный приоритет +3, остальные +1, нет в приоритетах 0
    if goals.priorities:
        if talk.track == goals.priorities[0]:
            score += 3
        elif talk.track in goals.priorities:
            score += 1

    # Воркшоп (бонус только если wants_workshops)
    if goals.wants_workshops and talk.format == TalkFormat.workshop:
        score += 2

    # must_attend / avoid
    if talk.id in goals.must_attend:
        score += 100
    if talk.id in goals.avoid:
        score -= 100

    # Уровень: совпадение +1, соседний уровень +0.5 (мягкий бонус)
    ld = _level_distance(goals.experience_level, talk.level)
    if ld == 0:
        score += 1
    elif ld == 1:
        score += 0.5

    # Язык: mismatch −3
    if goals.language_pref != LanguagePref.any and talk.language != goals.language_pref.value:
        score -= 3

    # Walking: штраф за смену зала между последовательными слотами
    if prev_room is not None and talk.room != prev_room:
        score += _walking_penalty(goals.max_walking)

    return score


def _is_lunch_overlap(talk: Talk, day_meta: ConferenceDay) -> bool:
    """True, если доклад пересекает обеденное окно."""
    return _overlaps(talk.start, talk.end, day_meta.lunch_start, day_meta.lunch_end)


# --------------------------------------------------------------------------- #
# Временные окна                                                              #
# --------------------------------------------------------------------------- #
def _get_windows(talks: list[Talk]) -> list[tuple[str, str]]:
    """Уникальные временные окна (start, end) по хронологии."""
    seen: set[tuple[str, str]] = set()
    windows: list[tuple[str, str]] = []
    for t in sorted(talks, key=lambda x: x.start):
        key = (t.start, t.end)
        if key not in seen:
            seen.add(key)
            windows.append(key)
    return windows


def _group_by_window(talks: list[Talk], windows: list[tuple[str, str]]) -> dict[tuple[str, str], list[Talk]]:
    """Группирует доклады по окнам."""
    groups: dict[tuple[str, str], list[Talk]] = {w: [] for w in windows}
    for t in talks:
        key = (t.start, t.end)
        if key in groups:
            groups[key].append(t)
    return groups


# --------------------------------------------------------------------------- #
# Построение дня                                                              #
# --------------------------------------------------------------------------- #
def _build_day(
    day: int,
    day_meta: ConferenceDay,
    talks: list[Talk],
    goals: UserGoals,
) -> RouteDay:
    windows = _get_windows(talks)
    groups = _group_by_window(talks, windows)

    # Фиксируем must_attend для этого дня
    must_ids = set(goals.must_attend)
    must_in_day: list[Talk] = [t for t in talks if t.id in must_ids and t.day == day]

    # Определяем блокированные окна (обед)
    lunch_windows: set[tuple[str, str]] = set()
    for t in talks:
        if _is_lunch_overlap(t, day_meta) and t.id not in must_ids:
            lunch_windows.add((t.start, t.end))

    # Жадный выбор по окнам
    slots: list[DaySlot] = []
    prev_room: Optional[str] = None

    for w_start, w_end in windows:
        candidates = groups.get((w_start, w_end), [])

        # Фильтруем: must_attend пропускаем фильтры, остальное — без avoid и обедных
        must_talks = [t for t in candidates if t.id in must_ids and t.day == day]
        other = [t for t in candidates if t.id not in must_ids]

        # Исключаем пересекающие обед (кроме must_attend)
        other = [t for t in other if not _is_lunch_overlap(t, day_meta)]

        if must_talks:
            # must_attend — выбираем первый (или лучший)
            best = must_talks[0]
            is_must = True
        else:
            # Скоринг и выбор лучшего
            scored: list[tuple[float, Talk]] = []
            for t in other:
                s = _score_talk(t, goals, prev_room)
                scored.append((s, t))
            scored.sort(key=lambda x: -x[0])

            # Бэктрекинг: если лучший имеет score < −50 — пропускаем окно
            if scored and scored[0][0] < -50:
                prev_room = None
                continue

            if not scored:
                prev_room = None
                continue

            best = scored[0][1]
            is_must = False

        # Конфликты: другие доклады этого окна (кроме must в must_attend)
        conflicts = [t.id for t in candidates if t.id != best.id and t.id not in must_ids]

        # lunch-конфликт
        lunch_conflict = False
        if is_must and _is_lunch_overlap(best, day_meta):
            lunch_conflict = True

        # Reason (fallback)
        reason = _make_reason(best, goals, is_must=is_must, lunch_conflict=lunch_conflict)

        # walking: обновляем prev_room
        prev_room = best.room

        slots.append(DaySlot(
            type=SlotType.talk,
            time=f"{best.start}–{best.end}",
            talk=best,
            reason=reason,
            conflicts=conflicts[:5],  # ограничим для читаемости
        ))

    # Вставка lunch-слота
    lunch_slot = DaySlot(
        type=SlotType.lunch,
        time=f"{day_meta.lunch_start}–{day_meta.lunch_end}",
        talk=None,
        reason="Обеденный перерыв — 1 час по требованию.",
        conflicts=[],
    )
    # Вставляем после последнего слота до 13:00 и до первого после 14:00
    lunch_idx = len(slots)
    for i, s in enumerate(slots):
        if s.talk and _time_to_min(s.talk.end) <= _time_to_min(day_meta.lunch_start):
            lunch_idx = i + 1
        elif s.talk and _time_to_min(s.talk.start) >= _time_to_min(day_meta.lunch_end):
            lunch_idx = i
            break

    slots.insert(lunch_idx, lunch_slot)

    return RouteDay(day=day, slots=slots)


# --------------------------------------------------------------------------- #
# Fallback-объяснения                                                         #
# --------------------------------------------------------------------------- #
def _make_reason(
    talk: Talk,
    goals: UserGoals,
    *,
    is_must: bool = False,
    lunch_conflict: bool = False,
) -> str:
    """Генерирует объяснение выбора через шаблоны (fallback, раздел 4.3 ТЗ)."""
    parts: list[str] = []
    track_label = TRACK_LABELS.get(talk.track, talk.track)

    if is_must:
        parts.append("Обязательный доклад — вы отметили его заранее.")
        parts.append(f"Тема «{track_label}».")
    elif goals.priorities and talk.track == goals.priorities[0]:
        parts.append(f"Главный приоритет — тема «{track_label}» (+3).")
    elif talk.track in goals.priorities:
        parts.append(f"Тема «{track_label}» — второстепенный приоритет (+1).")
    else:
        parts.append(
            f"Тема «{track_label}» вне ваших приоритетов — "
            "лучшая свободная активность в этом слоте."
        )

    # Уровень
    ld = _level_distance(goals.experience_level, talk.level)
    if ld == 0:
        parts.append("Уровень доклада совпадает с вашим.")
    elif ld == 1:
        parts.append("Уровень доклада близок к вашему.")

    # Формат
    if talk.format == TalkFormat.workshop:
        if goals.wants_workshops:
            parts.append("Формат — мастер-класс, вы отметили интерес к воркшопам.")
        else:
            parts.append("Формат — мастер-класс.")

    # Язык
    if talk.language == "en" and goals.language_pref != LanguagePref.en:
        parts.append("Доклад на английском языке.")

    # lunch conflict
    if lunch_conflict:
        parts.append("⚠ Внимание: доклад пересекается с обеденным перерывом.")

    return " ".join(parts) if parts else f"Доклад по теме «{track_label}»."


# --------------------------------------------------------------------------- #
# overall_strategy                                                            #
# --------------------------------------------------------------------------- #
def _build_strategy(goals: UserGoals, days: list[RouteDay]) -> str:
    """2–3 предложения от агента (fallback, раздел 4.3 ТЗ)."""
    priority_labels = [TRACK_LABELS.get(t, t) for t in goals.priorities[:2]]
    parts = [f"Маршрут сфокусирован на темах «{'» и «'.join(priority_labels)}»."]

    workshops_count = sum(
        1 for d in days for s in d.slots if s.type == SlotType.talk and s.talk and s.talk.format == TalkFormat.workshop
    )
    if workshops_count:
        parts.append(f"Включено {workshops_count} мастер-классов.")

    # lunch conflicts
    has_lunch_conflict = any(
        "пересекается с обеденным перерывом" in s.reason
        for d in days for s in d.slots
    )
    if has_lunch_conflict:
        parts.append(
            "Один must-attend конфликтует с обедом — оставлен с предупреждением."
        )

    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Публичный API                                                               #
# --------------------------------------------------------------------------- #
def build_route(goals: UserGoals) -> Route:
    """Построить персональный маршрут по целям участника."""
    days_meta = store.get_days()
    route_id = store.new_route_id()
    route_days: list[RouteDay] = []

    for dm in days_meta:
        talks = store.talks_for_day(dm.day)
        route_days.append(_build_day(dm.day, dm, talks, goals))

    strategy = _build_strategy(goals, route_days)
    route = Route(
        route_id=route_id,
        goals=goals,
        days=route_days,
        overall_strategy=strategy,
    )
    store.save_route(route)
    return route
