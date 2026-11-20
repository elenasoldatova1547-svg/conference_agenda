import type { Program, Route, TrackInfo, UserGoals } from './types'

/** Адрес API не задаётся в коде — относительный путь /api/*,
 * который Next.js проксирует на бэкенд через rewrites в next.config.ts. */

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(0, 'Сервис недоступен.')
  }

  if (!res.ok) {
    let detail = `Ошибка ${res.status}`
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') detail = data.detail
      else if (Array.isArray(data.detail)) detail = 'Проверьте корректность полей формы'
    } catch {
      /* тело не JSON — оставляем статус */
    }
    throw new ApiError(res.status, detail)
  }
  return (await res.json()) as T
}

export const fetchTracks = () => request<TrackInfo[]>('/api/tracks')
export const fetchProgram = () => request<Program>('/api/program')
export const postRoute = (goals: UserGoals) =>
  request<Route>('/api/route', { method: 'POST', body: JSON.stringify(goals) })
