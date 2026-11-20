"""Опциональная интеграция с LLM для объяснений (раздел 1 ТЗ).

По умолчанию выключена: объяснения формирует движок шаблонами (fallback).
Чтобы включить, задайте переменные окружения:
    LLM_ENABLED=1
    LLM_API_BASE=https://.../v1      # OpenAI-совместимый endpoint
    LLM_API_KEY=...
    LLM_MODEL=...

При любой ошибке или таймауте вызывающий код остаётся на fallback-текстах,
поэтому SLA «< 3 с без LLM» выполняется всегда.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import Route, UserGoals

_TIMEOUT = 8  # секунд; учитывается в SLA «< 10 с с LLM»


def is_enabled() -> bool:
    return os.getenv("LLM_ENABLED", "").lower() in ("1", "true", "yes") and bool(
        os.getenv("LLM_API_KEY")
    )


def enrich_route(route: Route, goals: UserGoals) -> Route:
    """Пытается обогатить overall_strategy через LLM. Без исключений.

    Возвращает тот же Route; при неудаче overall_strategy остаётся fallback.
    """
    if not is_enabled():
        return route

    api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    prompt = (
        "Ты — ассистент конференции AnalystDays. Сформулируй 2–3 предложения "
        "стратегии маршрута для участника. Приоритеты: "
        f"{[p.value for p in goals.priorities]}, уровень: "
        f"{goals.experience_level.value}. Ответь коротко по-русски."
    )
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 200,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = payload["choices"][0]["message"]["content"].strip()
        if text:
            route.overall_strategy = text
    except (urllib.error.URLError, KeyError, TimeoutError, ValueError):
        # fallback — оставляем шаблонную стратегию из движка
        pass

    return route
