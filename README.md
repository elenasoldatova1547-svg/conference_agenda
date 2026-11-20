# Маршрут для участника конференции — Frontend

Хакатонный прототип веб-сайта для конференции **AnalystDays** (2 дня, параллельные
секции). По целям участника строится персональное расписание на 2 дня с объяснением,
почему выбран каждый доклад, что пропущено и где обед.

Это **frontend**-репозиторий: **React / Vite / TypeScript**.
Backend (FastAPI + движок маршрута + Swagger + диаграммы) — в отдельном репозитории:
<https://github.com/elenasoldatova1547-svg/conference-agenda-back>

---

## Структура

```
index.html          точка входа, <title> «Маршрут для участника конференции»
vite.config.ts      dev-сервер + прокси /api → localhost:8000
src/
  App.tsx           оркестрация состояний (idle/loading/error/success)
  main.tsx          монтирование React
  api.ts            клиент API (+ VITE_API_BASE для прод-сборки)
  types.ts          TypeScript-типы по моделям бэкенда
  styles.css        пастельная дизайн-система (токены из ТЗ)
  components/
    Header.tsx      шапка сайта (BR-01)
    GoalsForm.tsx   форма целей: 7 тем, уровень, must-attend (BR-02)
    RouteTimeline.tsx  таймлайн маршрута: стратегия, слоты, обед (BR-04/05)
```

## Запуск

```bash
npm install
npm run dev        # http://localhost:5173
```

Frontend обращается к API через относительные пути `/api/*` — в dev-режиме
Vite проксирует их на backend (`http://localhost:8000`). Сначала запустите
backend из репозитория `conference-agenda-back`:

```bash
cd conference-agenda-back
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Сборка для продакшена

```bash
npm run build      # tsc --noEmit + vite build → dist/
```

При деплое укажите адрес API через переменную окружения `VITE_API_BASE`
(по умолчанию — относительные пути, когда фронт и API проксируются вместе).

## Соответствие требованиям ТЗ

| № | Критерий | Где реализовано |
|---|----------|-----------------|
| 1 | Заголовок «Маршрут для участника конференции» | `<title>` в `index.html`, `Header.tsx` |
| 2 | Ровно 7 тем | чекбоксы в `GoalsForm` (справочник `/api/tracks`) |
| 3 | Пастельная палитра | токены в `styles.css` (#FAF7F2, #A8C3B0, #C9D6E8) |
| 4 | Маршрут справа от формы (≥1024px) | `.layout` grid 2fr/3fr, sticky-колонка |
| 5 | Мобильный стек: форма сверху, маршрут снизу | media-query в `.layout` |
| 6 | Состояния loading/error/success | `App.tsx` + `RouteTimeline.tsx` (скелетон, «Повторить») |

---

## Деплой на RelaxDev (frontend)

Фронтенд собирается в Docker-образ с nginx, который раздаёт статику и проксирует
`/api/*` на бэкенд. Это необходимо: RelaxDev не читает `vercel.json` и не делает
rewrite на своей стороне — трафик сразу попадает в контейнер.

### Что настраивается

| Файл | Назначение |
|------|------------|
| `rewrites.json` | Адрес бэкенда: `https://conference-agenda-back.relaxdev.ru` |
| `scripts/bake-rewrites.mjs` | Подставляет адрес в шаблон nginx |
| `nginx.conf.template` | Шаблон конфигурации nginx с плейсхолдером `__BACKEND_URL__` |
| `Dockerfile` | Сборка: `node:20` собирает Vite, `nginx:1.27` раздаёт статику |

### Панель RelaxDev

1. Новый проект из этого репозитория, стек — **«Свой Dockerfile»**, путь к Dockerfile — корень.
2. Переменные окружения **не добавлять** (адрес бэкенда зашивается в образ на сборке).
3. Деплой. После любой правки `rewrites.json` или `nginx.conf.template` — полный редеплой без кэша Docker.

### Проверка после деплоя

- Открыть `https://conference-agenda.relaxdev.ru`, DevTools → Network → запрос `/api/health`
  должен вернуть JSON `{"status":"ok"}`.
- Swagger доступен по `/api/docs` (проксируется nginx'ом на Swagger бэкенда).
