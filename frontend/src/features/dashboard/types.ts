export interface DashboardStats {
  total_events: number
  total_links: number
  total_clicks: number
  events_today: number
}

export interface EventDay {
  date: string
  count: number
}

export interface TopUrl {
  url: string
  clicks: number
}
