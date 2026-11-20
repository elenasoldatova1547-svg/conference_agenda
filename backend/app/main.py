"""Точка входа FastAPI: «Маршрут для участника конференции».

Запуск:
    cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8000 --reload

Swagger: http://localhost:8000/docs  (раздел 4.3 ТЗ — все 6 эндпоинтов)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router

app = FastAPI(
    title="Маршрут для участника конференции — API",
    version="1.0.0",
    description=(
        "API для построения персонального маршрута по конференции AnalystDays. "
        "Поддерживает 7 фиксированных тем, обязательный обеденный перерыв "
        "и объяснение выбора докладов."
    ),
    servers=[{"url": "http://localhost:8000", "description": "local"}],
)

# CORS — фронтенд на Vite (5173) обращается к API на 8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"], summary="Проверка живости сервиса")
def health() -> dict[str, str]:
    return {"status": "ok"}
