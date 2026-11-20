/** TypeScript-типы, соответствующие Pydantic-моделям бэкенда. */

export type Track = 'processes' | 'tools' | 'career' | 'ui_ux' | 'clients_cases' | 'architecture' | 'data'

export type TalkFormat = 'talk' | 'workshop' | 'roundtable'
export type Language = 'ru' | 'en'
export type Level = 'junior' | 'middle' | 'senior' | 'lead'
export type LanguagePref = 'ru' | 'en' | 'any'
export type Walking = 'low' | 'medium' | 'high'
export type SlotType = 'talk' | 'lunch' | 'networking'

export interface TrackInfo { code: Track; label: string }

export interface ConferenceDay {
  day: number
  lunch_start: string
  lunch_end: string
}

export interface Talk {
  id: string
  title: string
  speaker: string
  company: string
  track: Track
  day: number
  start: string
  end: string
  room: string
  format: TalkFormat
  language: Language
  level: Level
  tags: string[]
  description_short: string
}

export interface Program {
  days: ConferenceDay[]
  talks: Talk[]
}

export interface UserGoals {
  priorities: Track[]
  experience_level: Level
  wants_workshops: boolean
  max_walking: Walking
  must_attend: string[]
  avoid: string[]
  language_pref: LanguagePref
}

export interface DaySlot {
  type: SlotType
  time: string
  talk: Talk | null
  reason: string
  conflicts: string[]
}

export interface RouteDay {
  day: number
  slots: DaySlot[]
}

export interface Route {
  route_id: string
  goals: UserGoals
  days: RouteDay[]
  overall_strategy: string
}
