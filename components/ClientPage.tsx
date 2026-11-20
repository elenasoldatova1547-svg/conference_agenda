'use client'

import { useState, useEffect, useCallback } from 'react'
import type { Program, Route, TrackInfo, Track, UserGoals } from '../lib/types'
import GoalsForm from './GoalsForm'
import RouteTimeline from './RouteTimeline'
import { fetchTracks, fetchProgram, postRoute, ApiError } from '../lib/api'

type AppStatus = 'idle' | 'loading' | 'error' | 'success'

export default function ClientPage() {
  const [tracks, setTracks] = useState<TrackInfo[]>([])
  const [talks, setTalks] = useState<Program['talks']>([])
  const [status, setStatus] = useState<AppStatus>('idle')
  const [route, setRoute] = useState<Route | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastGoals, setLastGoals] = useState<UserGoals | null>(null)

  // Загрузка справочника тем и расписания при монтировании.
  useEffect(() => {
    let cancelled = false
    Promise.all([fetchTracks(), fetchProgram()])
      .then(([t, p]) => {
        if (cancelled) return
        setTracks(t)
        setTalks(p.talks)
      })
      .catch(() => {
        if (cancelled) return
        setStatus('error')
        setError('Не удалось загрузить данные конференции.')
      })
    return () => { cancelled = true }
  }, [])

  const handleBuild = useCallback((goals: UserGoals) => {
    setStatus('loading')
    setLastGoals(goals)
    postRoute(goals)
      .then((r) => {
        setRoute(r)
        setStatus('success')
        setError(null)
      })
      .catch((e) => {
        if (e instanceof ApiError) {
          setError(e.message)
        } else {
          setError('Неизвестная ошибка при построении маршрута.')
        }
        setStatus('error')
      })
  }, [])

  const trackLabels: Record<Track, string> = Object.fromEntries(
    tracks.map((t) => [t.code, t.label]),
  ) as Record<Track, string>

  return (
    <main className="layout">
      {/* Левая колонка: форма целей (40%) */}
      <div className="form-panel">
        <div className="panel">
          <h2 className="panel__title">Ваши цели</h2>
          {tracks.length > 0 ? (
            <GoalsForm
              tracks={tracks}
              talks={talks}
              loading={status === 'loading'}
              hasRoute={status === 'success'}
              onBuild={handleBuild}
            />
          ) : (
            <div className="empty">Загрузка данных…</div>
          )}
        </div>
      </div>

      {/* Правая колонка: маршрут (60%) — sticky на десктопе (BR-04) */}
      <div className="result-panel">
        <div className="panel">
          <h2 className="panel__title">Маршрут</h2>
          <RouteTimeline
            status={status}
            route={route}
            error={error}
            trackLabels={trackLabels}
            onRetry={() => lastGoals && handleBuild(lastGoals)}
          />
        </div>
      </div>
    </main>
  )
}
