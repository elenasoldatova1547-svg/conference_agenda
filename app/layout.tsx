import type { Metadata } from 'next'
import './globals.css'

// BR-01: заголовок сайта строго «Маршрут для участника конференции»
export const metadata: Metadata = {
  title: 'Маршрут для участника конференции',
  description: 'Персональный маршрут по конференции AnalystDays',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}
