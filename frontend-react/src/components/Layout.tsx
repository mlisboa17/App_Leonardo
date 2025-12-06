import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { 
  LayoutDashboard, Activity, History, Settings, 
  LogOut, Bot, User, Bell, AlertOctagon, Zap 
} from 'lucide-react'
import { actionsApi } from '../services/api'
import { useState } from 'react'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [showEmergency, setShowEmergency] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleEmergencyStop = async () => {
    if (!confirm('🚨 PARADA DE EMERGÊNCIA!\n\nIsso vai PARAR todos os bots imediatamente.\n\nTem certeza?')) return
    
    try {
      await actionsApi.emergencyStop()
      alert('Parada de emergência ativada!')
    } catch (error) {
      alert('Erro ao ativar parada de emergência')
    }
  }

  const navItems = [
    { to: '/', icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard' },
    { to: '/positions', icon: <Activity className="w-5 h-5" />, label: 'Posições' },
    { to: '/trades', icon: <History className="w-5 h-5" />, label: 'Histórico' },
    { to: '/bots', icon: <Zap className="w-5 h-5" />, label: 'Controle Bots' },
    { to: '/config', icon: <Settings className="w-5 h-5" />, label: 'Config' },
  ]

  return (
    <div className="min-h-screen bg-dark-300 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-200 border-r border-gray-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white">R7 Trading</h1>
              <p className="text-xs text-gray-400">Dashboard v1.0</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-400 hover:bg-dark-100 hover:text-white'
                }`
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Emergency Button */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={handleEmergencyStop}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors"
          >
            <AlertOctagon className="w-5 h-5" />
            <span className="font-medium">Emergência</span>
          </button>
        </div>

        {/* User */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-300" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white truncate">{user?.username}</p>
              <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-100 rounded-lg transition-colors"
              title="Sair"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="h-16 bg-dark-200 border-b border-gray-700 flex items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-400">Sistema Online</span>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-gray-400 hover:text-white hover:bg-dark-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-6 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
