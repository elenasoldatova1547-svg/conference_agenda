# Маршрут для участника конференции

Хакатонный прототип веб-сайта для конференции **AnalystDays** (2 дня, параллельные
секции). По целям участника строится персональное расписание на 2 дня с объяснением,
почему выбран каждый доклад, что пропущено и где обед.

Стек: **FastAPI** (backend) + **React / Vite / TypeScript** (frontend), мок-расписание
в `program.json`, LLM опционален (есть fallback на шаблоны).

---

## Структура репозитория

```
backend/            FastAPI-сервис и движок маршрута
  app/
    main.py         точка входа, CORS, /health, Swagger
    api.py          эндпоинты /api/*
    models.py       Pydantic-модели (ERD ТЗ)
    engine.py       скоринг + построение маршрута + fallback-тексты
    llm.py          опциональная LLM-интеграция (по умолчанию выключена)
    store.py        загрузка program.json + кэш маршрутов
    data/program.json   мок-расписание (48 докладов, 2 дня, обед 13:00–14:00)
  scripts/generate_program.py   генератор program.json
frontend/           React + Vite + TypeScript
  src/
    App.tsx         оркестрация состояний (idle/loading/error/success)
    components/     Header, GoalsForm (7 тем), RouteTimeline (таймлайн)
    api.ts          клиент API
    styles.css      пастельная дизайн-система (токены из ТЗ)
docs/               PlantUML: ERD_Route, BPMN_Route_Real, Seq_Route_Real
```

---

## Запуск

### 1. Backend (порт 8000)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# (опционально) перегенерировать мок-расписание:
python backend/scripts/generate_program.py

cd backend
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs> — содержит все 6 эндпоинтов.
- Health-check: <http://localhost:8000/health>

### 2. Frontend (порт 5173)

В отдельном терминале:

```bash
cd frontend
npm install
npm run dev
```

Открыть <http://localhost:5173>. В dev-режиме Vite проксирует `/api` и `/health`
на backend (порт 8000), поэтому CORS не требуется.

### Сборка фронтенда для продакшена

```bash
cd frontend && npm run build   # tsc --noEmit + vite build → dist/
```

---

## API

| Метод | Путь                  | Назначение                          |
|-------|-----------------------|-------------------------------------|
| GET   | `/api/program`        | Полное расписание на 2 дня          |
| GET   | `/api/tracks`         | Справочник 7 тем                    |
| GET   | `/api/talk/{id}`      | Детали доклада по ID                |
| POST  | `/api/route`          | Построить маршрут по целям          |
| GET   | `/api/route/{id}`     | Получить сохранённый маршрут        |
| GET   | `/health`             | Проверка живости сервиса            |

Пример:

```bash
curl -X POST localhost:8000/api/route \
  -H 'Content-Type: application/json' \
  -d '{"priorities":["career","data"],"experience_level":"junior","wants_workshops":true}'
```

---

## Как работает движок маршрута

1. **Скоринг докладов:** +3 главный трек (первый в приоритетах), +1 второстепенный,
   +2 мастер-класс (если запрошены), +100 `must_attend`, −100 `avoid`, бонус за
   совпадение уровня, штраф за язык и за переходы между залами (учитывает
   `max_walking`).
2. **Фиксация `must_attend`** — обязательные доклады всегда попадают в маршрут.
3. **Блокировка обеда** — доклады, пересекающие `13:00–14:00`, исключаются
   (кроме `must_attend`, для которых ставится `conflict_reason`).
4. **Жадный выбор по временным слотам** с бэктрекингом (окно пропускается, если
   лучший кандидат слишком плох).
5. **Объяснения** — fallback-шаблоны; при включённом LLM (`LLM_ENABLED=1`)
   переписывается `overall_strategy`.

---

## Соответствие критериям приёмки (ТЗ, раздел 8)

| № | Критерий | Где реализовано |
|---|----------|-----------------|
| 1 | Заголовок «Маршрут для участника конференции» | `<title>` в `index.html`, `Header.tsx` |
| 2 | Ровно 7 тем | `models.Track`, `/api/tracks`, чекбоксы `GoalsForm` |
| 3 | Пастельная палитра | токены в `styles.css` |
| 4 | Маршрут справа от формы (≥1024px) | `.layout` grid 2fr/3fr |
| 5 | Обед 1 час/день, без пересечений | `engine._build_day`, lunch-слот |
| 6 | POST /api/route < 3 с без LLM | движок на чистом Python, LLM выключен |
| 7 | Swagger на /docs, 6 эндпоинтов | FastAPI, проверено через `/openapi.json` |
| 8 | Смена приоритетов меняет маршрут | скоринг по `priorities` |
| 9 | ERD/BPMN/Sequence в репозитории | `docs/*.puml` |
| 10 | Демо «Junior, карьера + мастер-классы» | приоритет career + wants_workshops |

---

## Опционально: включить LLM

```bash
export LLM_ENABLED=1
export LLM_API_BASE=https://<openai-совместимый-endpoint>/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

При любой ошибке/таймауте система автоматически остаётся на шаблонных объяснениях.
