import { create } from 'zustand'
import { authApi } from '../services/api'

interface User {
  id: number
  username: string
  role: string
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authApi.login(username, password)
      const { access_token, user } = response.data
      
      localStorage.setItem('token', access_token)
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      set({
        error: err.response?.data?.detail || 'Erro ao fazer login',
        isLoading: false,
      })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ isAuthenticated: false })
      return
    }

    try {
      const response = await authApi.me()
      set({
        user: response.data,
        isAuthenticated: true,
      })
    } catch {
      localStorage.removeItem('token')
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      })
    }
  },
}))
