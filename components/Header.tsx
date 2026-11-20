export default function Header() {
  return (
    <header className="header">
      <div className="header__inner">
        {/* BR-01: заголовок строго «Маршрут для участника конференции» */}
        <h1 className="header__title">Маршрут для участника конференции</h1>
        <p className="header__subtitle">
          AnalystDays · персональное расписание на 2 дня с объяснением выбора
        </p>
      </div>
    </header>
  )
}
