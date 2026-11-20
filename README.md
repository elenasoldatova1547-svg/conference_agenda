# Маршрут для участника конференции — Frontend

Хакатонный прототип веб-сайта для конференции **AnalystDays** (2 дня, параллельные
секции). По целям участника строится персональное расписание на 2 дня с объяснением,
почему выбран каждый доклад, что пропущено и где обед.

Это **frontend**-репозиторий: **Next.js (App Router) / React 19 / TypeScript**.
Backend (FastAPI + движок маршрута + Swagger + диаграммы) — в отдельном репозитории:
<https://github.com/elenasoldatova1547-svg/conference-agenda-back>

---

## Структура

```
app/
  layout.tsx      корневой layout: metadata.title = «Маршрут для участника конференции» (BR-01)
  page.tsx        корневая страница → ClientPage (use client)
  globals.css     пастельная дизайн-система (токены из ТЗ)
components/
  ClientPage.tsx  оркестрация состояний (idle/loading/error/success)
  GoalsForm.tsx   форма целей: 7 тем, уровень, must-attend (BR-02)
  Header.tsx      шапка сайта (BR-01)
  RouteTimeline.tsx  таймлайн маршрута: стратегия, слоты, обед (BR-04/05)
lib/
  api.ts          клиент API (относительные пути /api/*)
  types.ts        TypeScript-типы по моделям бэкенда
rewrites.json     адрес бэкенда (единая точка правды, зашивается в образ)
next.config.ts    output: "standalone" + rewrites /api/* → бэкенд
Dockerfile        node:20 → standalone-сервер
```

## Запуск

```bash
npm install
npm run dev        # http://localhost:3000
```

Frontend обращается к API через относительные пути `/api/*` — Next.js проксирует
их на бэкенд через `rewrites()` в `next.config.ts`. Сначала запустите backend:

```bash
cd conference-agenda-back
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Соответствие требованиям ТЗ

| № | Критерий | Где реализовано |
|---|----------|-----------------|
| 1 | Заголовок «Маршрут для участника конференции» | `metadata.title` в `app/layout.tsx`, `Header.tsx` |
| 2 | Ровно 7 тем | чекбоксы в `GoalsForm` (справочник `/api/tracks`) |
| 3 | Пастельная палитра | токены в `app/globals.css` (#FAF7F2, #A8C3B0, #C9D6E8) |
| 4 | Маршрут справа от формы (≥1024px) | `.layout` grid 2fr/3fr, sticky-колонка |
| 5 | Мобильный стек: форма сверху, маршрут снизу | media-query в `.layout` |
| 6 | Состояния loading/error/success | `ClientPage` + `RouteTimeline` (скелетон, «Повторить») |

---

## Деплой на RelaxDev

### Почему standalone

Платформа RelaxDev в режиме автодетекта ищет `.next/standalone` (Next.js) или
`.output/server/index.mjs` (Nuxt). Это node-сервер, который сам слушает `PORT` и
проксирует `/api/*` через `rewrites()` в `next.config.ts`. nginx в контейнере не нужен.

### Что настраивается

| Файл | Назначение |
|------|------------|
| `rewrites.json` | Адрес бэкенда: `https://conference-agenda-back.relaxdev.ru` |
| `next.config.ts` | `output: "standalone"` + `rewrites()` читает rewrites.json |
| `Dockerfile` | `node:20` → standalone-сервер, `CMD node server.js` |

### Панель RelaxDev

1. Новый проект из этого репозитория, стек — **«Свой Dockerfile»**, путь к Dockerfile — корень.
2. Переменные окружения **не добавлять** (адрес бэкенда зашивается из `rewrites.json` на сборке).
3. Деплой. После любой правки `rewrites.json` — полный редеплой без кэша Docker.

### Проверка после деплоя

- Открыть `https://conference-agenda.relaxdev.ru`, DevTools → Network → запрос `/api/health`
  должен вернуть JSON `{"status":"ok"}`.
- Swagger доступен по `/api/docs` (проксируется Next.js на Swagger бэкенда).
