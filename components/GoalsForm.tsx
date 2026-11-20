'use client'

import { useMemo, useState } from 'react'
import type { Level, Talk, Track, TrackInfo, UserGoals, Walking, LanguagePref } from '../lib/types'

interface Props {
  tracks: TrackInfo[]
  talks: Talk[]
  loading: boolean
  hasRoute: boolean
  onBuild: (goals: UserGoals) => void
}

const LEVELS: { value: Level; label: string }[] = [
  { value: 'junior', label: 'Junior' },
  { value: 'middle', label: 'Middle' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
]

const WALKING: { value: Walking; label: string }[] = [
  { value: 'low', label: 'Низкая (меньше переходов)' },
  { value: 'medium', label: 'Средняя' },
  { value: 'high', label: 'Высокая (готов ходить много)' },
]

const LANGS: { value: LanguagePref; label: string }[] = [
  { value: 'any', label: 'Не важно' },
  { value: 'ru', label: 'Только русские' },
  { value: 'en', label: 'Только английские' },
]

export default function GoalsForm({ tracks, talks, loading, hasRoute, onBuild }: Props) {
  const [priorities, setPriorities] = useState<Track[]>([])
  const [experienceLevel, setExperienceLevel] = useState<Level>('junior')
  const [wantsWorkshops, setWantsWorkshops] = useState(false)
  const [maxWalking, setMaxWalking] = useState<Walking>('medium')
  const [languagePref, setLanguagePref] = useState<LanguagePref>('any')
  const [mustAttend, setMustAttend] = useState<string[]>([])
  const [avoid, setAvoid] = useState<string[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  // Список докладов для must_attend / avoid, сгруппированный по дням.
  const talkOptions = useMemo(() => {
    const byDay = new Map<number, Talk[]>()
    for (const t of talks) {
      if (!byDay.has(t.day)) byDay.set(t.day, [])
      byDay.get(t.day)!.push(t)
    }
    return [...byDay.entries()].sort((a, b) => a[0] - b[0])
  }, [talks])

  function toggleTrack(code: Track) {
    setPriorities((prev) =>
      prev.includes(code) ? prev.filter((t) => t !== code) : [...prev, code],
    )
  }

  function collectSelected(e: React.ChangeEvent<HTMLSelectElement>) {
    return Array.from(e.target.selectedOptions, (o) => o.value)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (priorities.length === 0) {
      setFormError('Выберите хотя бы одну тему — это обязательное поле.')
      return
    }
    setFormError(null)
    onBuild({
      priorities,
      experience_level: experienceLevel,
      wants_workshops: wantsWorkshops,
      max_walking: maxWalking,
      must_attend: mustAttend,
      avoid,
      language_pref: languagePref,
    })
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <fieldset>
        <legend>Интересующие темы ({priorities.length})</legend>
        {formError && <div className="form-error">{formError}</div>}
        <div className="tracks">
          {tracks.map((t) => (
            <label
              key={t.code}
              className={`track-check${priorities.includes(t.code) ? ' is-checked' : ''}`}
            >
              <input
                type="checkbox"
                checked={priorities.includes(t.code)}
                onChange={() => toggleTrack(t.code)}
              />
              <span>{t.label}</span>
            </label>
          ))}
        </div>
        <p className="hint">Порядок выбора важен: первая тема — главный приоритет (+3).</p>
      </fieldset>

      <fieldset>
        <legend>Опыт и формат</legend>
        <div className="row2">
          <div className="field">
            <label htmlFor="exp">Уровень</label>
            <select id="exp" value={experienceLevel} onChange={(e) => setExperienceLevel(e.target.value as Level)}>
              {LEVELS.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="lang">Язык докладов</label>
            <select id="lang" value={languagePref} onChange={(e) => setLanguagePref(e.target.value as LanguagePref)}>
              {LANGS.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label htmlFor="walk">Готовность к переходам между залами</label>
          <select id="walk" value={maxWalking} onChange={(e) => setMaxWalking(e.target.value as Walking)}>
            {WALKING.map((w) => (
              <option key={w.value} value={w.value}>{w.label}</option>
            ))}
          </select>
        </div>

        <label className="switch">
          <input
            type="checkbox"
            checked={wantsWorkshops}
            onChange={(e) => setWantsWorkshops(e.target.checked)}
          />
          Включить мастер-классы (workshop)
        </label>
      </fieldset>

      <fieldset>
        <legend>Обязательные доклады и антипатии</legend>
        <div className="field">
          <label htmlFor="must">Must attend (обязательно)</label>
          <select
            id="must"
            multiple
            className="multiselect"
            value={mustAttend}
            onChange={(e) => setMustAttend(collectSelected(e))}
          >
            {talkOptions.map(([day, list]) => (
              <optgroup key={day} label={`День ${day}`}>
                {list.map((t) => (
                  <option key={t.id} value={t.id}>{t.start} · {t.title}</option>
                ))}
              </optgroup>
            ))}
          </select>
          <p className="hint">Ctrl/Cmd + клик — выбрать несколько.</p>
        </div>
        <div className="field">
          <label htmlFor="avoid">Не посещать (avoid)</label>
          <select
            id="avoid"
            multiple
            className="multiselect"
            value={avoid}
            onChange={(e) => setAvoid(collectSelected(e))}
          >
            {talkOptions.map(([day, list]) => (
              <optgroup key={day} label={`День ${day}`}>
                {list.map((t) => (
                  <option key={t.id} value={t.id}>{t.start} · {t.title}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
      </fieldset>

      <button type="submit" className="btn btn--primary" disabled={loading}>
        {loading ? 'Строим маршрут…' : hasRoute ? 'Перестроить маршрут' : 'Построить маршрут'}
      </button>
    </form>
  )
}
