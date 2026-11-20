import type { Program, Route, TrackInfo, UserGoals } from './types'

/** Базовый URL API. В dev пустой → относительные пути идут через Vite-прокси. */
const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

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
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(0, 'Сервис недоступен. Проверьте, что backend запущен на порту 8000.')
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
