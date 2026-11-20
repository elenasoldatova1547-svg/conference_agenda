import type { Route, Track } from '../types'

type Status = 'idle' | 'loading' | 'error' | 'success'

interface Props {
  status: Status
  route: Route | null
  error: string | null
  trackLabels: Record<Track, string>
  onRetry: () => void
}

const FORMAT_LABEL: Record<string, string> = {
  talk: 'Доклад',
  workshop: 'Мастер-класс',
  roundtable: 'Круглый стол',
}

function StrategyBanner({ text }: { text: string }) {
  return (
    <div className="strategy">
      <div className="strategy__label">Стратегия маршрута</div>
      <p className="strategy__text">{text}</p>
    </div>
  )
}

function TalkCard({ slot, trackLabels, mustIds }: {
  slot: Route['days'][number]['slots'][number]
  trackLabels: Record<Track, string>
  mustIds: Set<string>
}) {
  const talk = slot.talk!
  const isMust = mustIds.has(talk.id)
  const lunchConflict = /пересекается с обед/i.test(slot.reason)

  return (
    <div className="slot" data-track={talk.track}>
      <div className="slot__time">{slot.time}</div>
      <div className="talk-card">
        <div className="talk-card__head">
          <h4 className="talk-card__title">{talk.title}</h4>
          <div className="badges">
            <span className="badge badge--track">{trackLabels[talk.track] ?? talk.track}</span>
            <span className="badge badge--format">{FORMAT_LABEL[talk.format] ?? talk.format}</span>
            {talk.language === 'en' && <span className="badge badge--format">EN</span>}
            {isMust && <span className="badge badge--must">Must attend</span>}
            {lunchConflict && <span className="badge badge--conflict">Пересечение с обедом</span>}
          </div>
        </div>
        <p className="talk-card__meta">
          {talk.speaker}
          {talk.company ? ` · ${talk.company}` : ''} · {talk.room} · {talk.level}
        </p>
        {slot.reason && <p className="talk-card__reason">{slot.reason}</p>}
        {slot.conflicts.length > 0 && (
          <div className="badges" style={{ marginTop: 8 }}>
            <span className="badge badge--conflict">
              Пропущено параллельных: {slot.conflicts.length}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function LunchSlot({ slot }: { slot: Route['days'][number]['slots'][number] }) {
  return (
    <div className="slot slot--lunch">
      <div className="slot__time">{slot.time}</div>
      <div className="talk-card">
        <h4 className="talk-card__title">🍽 Обед</h4>
      </div>
    </div>
  )
}

function Skeleton() {
  return (
    <div className="skeleton" aria-hidden>
      <div className="sk-line sk-line--short" />
      <div className="sk-card" />
      <div className="sk-card" />
      <div className="sk-card" />
    </div>
  )
}

export default function RouteTimeline({ status, route, error, trackLabels, onRetry }: Props) {
  if (status === 'loading') return <Skeleton />

  if (status === 'error') {
    return (
      <div className="error-box">
        <p>{error ?? 'Не удалось построить маршрут.'}</p>
        <button className="btn btn--ghost" onClick={onRetry}>Повторить</button>
      </div>
    )
  }

  if (status !== 'success' || !route) {
    return (
      <div className="empty">
        Заполните цели слева и нажмите «Построить маршрут» — здесь появится
        персональное расписание на 2 дня.
      </div>
    )
  }

  const mustIds = new Set(route.goals.must_attend)

  return (
    <div>
      <StrategyBanner text={route.overall_strategy} />
      {route.days.map((d) => (
        <section className="day" key={d.day}>
          <h3 className="day__title">День {d.day}</h3>
          {d.slots.map((s, i) =>
            s.type === 'talk' && s.talk ? (
              <TalkCard key={`${d.day}-${i}`} slot={s} trackLabels={trackLabels} mustIds={mustIds} />
            ) : (
              <LunchSlot key={`${d.day}-${i}`} slot={s} />
            ),
          )}
        </section>
      ))}
    </div>
  )
}
