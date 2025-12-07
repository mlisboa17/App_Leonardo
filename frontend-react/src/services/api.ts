import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
  changePassword: (newPassword: string) =>
    api.put('/auth/me/password', null, { params: { new_password: newPassword } }),
  getUsers: () => api.get('/auth/users'),
  createUser: (data: { username: string; password: string; role: string }) =>
    api.post('/auth/users', data),
  deleteUser: (username: string) => api.delete(`/auth/users/${username}`),
}

// Dashboard
export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary'),
  getDailyStats: (days = 30) => api.get('/dashboard/stats/daily', { params: { days } }),
  getPositions: (page = 1, perPage = 20) =>
    api.get('/dashboard/positions', { params: { page, per_page: perPage } }),
  getTrades: (page = 1, perPage = 50) =>
    api.get('/dashboard/trades', { params: { page, per_page: perPage } }),
  getBotsStatus: () => api.get('/dashboard/bots/status'),
  getPnlChart: (period = '30d') => api.get('/dashboard/chart/pnl', { params: { period } }),
  getIndicators: () => api.get('/dashboard/indicators'),
  getBotComparison: () => api.get('/dashboard/comparison'),
}

// Config
export const configApi = {
  getAll: () => api.get('/config/all'),
  getGlobal: () => api.get('/config/global'),
  updateGlobal: (updates: Record<string, unknown>) => api.put('/config/global', updates),
  getBots: () => api.get('/config/bots'),
  getBot: (name: string) => api.get(`/config/bots/${name}`),
  updateBot: (name: string, updates: Record<string, unknown>) =>
    api.put(`/config/bots/${name}`, updates),
  enableBot: (name: string) => api.post(`/config/bots/${name}/enable`),
  disableBot: (name: string) => api.post(`/config/bots/${name}/disable`),
}

// Actions
export const actionsApi = {
  getStatus: () => api.get('/actions/status'),
  startBot: (botName?: string) =>
    api.post('/actions/bot/start', null, { params: { bot_name: botName } }),
  stopBot: (botName?: string) =>
    api.post('/actions/bot/stop', null, { params: { bot_name: botName } }),
  restartBot: (botName?: string) =>
    api.post('/actions/bot/restart', null, { params: { bot_name: botName } }),
  emergencyStop: () => api.post('/actions/emergency/stop'),
  clearEmergency: () => api.post('/actions/emergency/clear'),
  liquidateAll: (confirm = false) =>
    api.post('/actions/liquidate/all', null, { params: { confirm } }),
  closePosition: (positionId: number, reason?: string) =>
    api.post(`/actions/position/${positionId}/close`, null, { params: { reason } }),
}

export default api
