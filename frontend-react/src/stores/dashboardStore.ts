import { create } from 'zustand'
import { dashboardApi, actionsApi } from '../services/api'

interface BotStatus {
  name: string
  status: string
  pnl_today: number
  pnl_total: number
  trades_today: number
  win_rate: number
  open_positions: number
  capital_allocated: number
}

interface Position {
  id: number
  bot_name: string
  symbol: string
  side: string
  entry_price: number
  current_price: number
  quantity: number
  pnl: number
  pnl_percent: number
  opened_at: string
}

interface DashboardSummary {
  total_balance: number
  available_balance: number
  in_positions: number
  pnl_today: number
  pnl_week: number
  pnl_month: number
  total_trades: number
  active_bots: number
  open_positions: number
  win_rate: number
}

interface DashboardState {
  summary: DashboardSummary | null
  bots: BotStatus[]
  positions: Position[]
  isLoading: boolean
  error: string | null
  fetchSummary: () => Promise<void>
  fetchBots: () => Promise<void>
  fetchPositions: () => Promise<void>
  startBot: (name?: string) => Promise<void>
  stopBot: (name?: string) => Promise<void>
}

export const useDashboardStore = create<DashboardState>((set) => ({
  summary: null,
  bots: [],
  positions: [],
  isLoading: false,
  error: null,

  fetchSummary: async () => {
    set({ isLoading: true })
    try {
      const response = await dashboardApi.getSummary()
      set({ summary: response.data, isLoading: false })
    } catch (error) {
      set({ error: 'Erro ao carregar resumo', isLoading: false })
    }
  },

  fetchBots: async () => {
    try {
      const response = await dashboardApi.getBotsStatus()
      set({ bots: response.data.bots || [] })
    } catch (error) {
      set({ error: 'Erro ao carregar bots' })
    }
  },

  fetchPositions: async () => {
    try {
      const response = await dashboardApi.getPositions()
      set({ positions: response.data.items || [] })
    } catch (error) {
      set({ error: 'Erro ao carregar posições' })
    }
  },

  startBot: async (name?: string) => {
    try {
      await actionsApi.startBot(name)
    } catch (error) {
      set({ error: 'Erro ao iniciar bot' })
    }
  },

  stopBot: async (name?: string) => {
    try {
      await actionsApi.stopBot(name)
    } catch (error) {
      set({ error: 'Erro ao parar bot' })
    }
  },
}))
