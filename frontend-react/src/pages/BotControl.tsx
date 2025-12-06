import { useState, useEffect } from 'react'
import { 
  Bot, Power, PowerOff, Zap, AlertTriangle, 
  Settings, RefreshCw, CheckCircle, XCircle,
  ArrowRight, Shield
} from 'lucide-react'

interface BotControl {
  name: string
  bot_type: string
  enabled: boolean
  status: string
  win_rate: number
  total_trades: number
  pnl_today: number
  open_positions: number
}

interface UniBotStatus {
  enabled: boolean
  name: string
  portfolio_size: number
  strategy: string
}

export default function BotControl() {
  const [bots, setBots] = useState<BotControl[]>([])
  const [uniBot, setUniBot] = useState<UniBotStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)

  const fetchBots = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/bots/control', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setBots(data.bots || [])
      setUniBot(data.unico_bot || null)
    } catch (error) {
      console.error('Erro ao carregar bots:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBots()
    const interval = setInterval(fetchBots, 10000)
    return () => clearInterval(interval)
  }, [])

  const toggleBot = async (botType: string, enable: boolean) => {
    setActionLoading(botType)
    setMessage(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/bots/control/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ bot_type: botType, enabled: enable })
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setMessage({ type: 'success', text: data.message || `Bot ${enable ? 'ativado' : 'pausado'} com sucesso!` })
        fetchBots()
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao alterar bot' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro de conexão' })
    } finally {
      setActionLoading(null)
    }
  }

  const activateUnicoBot = async () => {
    if (!confirm('⚠️ ATENÇÃO: Ao ativar o UnicoBot, TODOS os outros bots serão DESATIVADOS.\n\nO UnicoBot assumirá controle total de todas as carteiras.\n\nDeseja continuar?')) {
      return
    }
    
    setActionLoading('unico_bot')
    setMessage(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/bots/control/unico-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ enabled: true })
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setMessage({ type: 'success', text: '🤖 UnicoBot ATIVADO! Todos os outros bots foram pausados.' })
        fetchBots()
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao ativar UnicoBot' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro de conexão' })
    } finally {
      setActionLoading(null)
    }
  }

  const deactivateUnicoBot = async () => {
    setActionLoading('unico_bot')
    setMessage(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/bots/control/unico-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ enabled: false })
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'UnicoBot desativado. Você pode ativar os bots especializados novamente.' })
        fetchBots()
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao desativar UnicoBot' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro de conexão' })
    } finally {
      setActionLoading(null)
    }
  }

  const restartSystem = async () => {
    if (!confirm('⚠️ Isso irá REINICIAR todo o sistema de bots.\n\nAs posições abertas serão mantidas.\n\nDeseja continuar?')) {
      return
    }
    
    setActionLoading('restart')
    setMessage(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/bots/control/restart', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setMessage({ type: 'success', text: '🔄 Sistema reiniciando... Aguarde alguns segundos.' })
        setTimeout(fetchBots, 5000)
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao reiniciar' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro de conexão' })
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Controle de Bots</h1>
          <p className="text-gray-400">Gerencie seus bots de trading</p>
        </div>
        <button
          onClick={restartSystem}
          disabled={actionLoading === 'restart'}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${actionLoading === 'restart' ? 'animate-spin' : ''}`} />
          Reiniciar Sistema
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${
          message.type === 'success' 
            ? 'bg-green-500/20 border border-green-500/50 text-green-400'
            : 'bg-red-500/20 border border-red-500/50 text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* UnicoBot Card */}
      <div className={`p-6 rounded-xl border-2 ${
        uniBot?.enabled 
          ? 'bg-gradient-to-br from-purple-900/50 to-blue-900/50 border-purple-500'
          : 'bg-dark-100 border-gray-700'
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${uniBot?.enabled ? 'bg-purple-500' : 'bg-gray-700'}`}>
              <Zap className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                UnicoBot
                {uniBot?.enabled && (
                  <span className="px-2 py-0.5 text-xs bg-purple-500 text-white rounded-full">ATIVO</span>
                )}
              </h2>
              <p className="text-gray-400">Bot unificado com Smart Strategy</p>
              <p className="text-sm text-gray-500 mt-1">
                Controla todas as carteiras • {uniBot?.portfolio_size || 12} moedas • {uniBot?.strategy || 'Smart Strategy v2.0'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {uniBot?.enabled ? (
              <button
                onClick={deactivateUnicoBot}
                disabled={actionLoading === 'unico_bot'}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {actionLoading === 'unico_bot' ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <PowerOff className="w-4 h-4" />
                )}
                Desativar
              </button>
            ) : (
              <button
                onClick={activateUnicoBot}
                disabled={actionLoading === 'unico_bot'}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition disabled:opacity-50 font-medium"
              >
                {actionLoading === 'unico_bot' ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Ativar UnicoBot
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        
        {!uniBot?.enabled && (
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-200">
              <strong>Atenção:</strong> Ao ativar o UnicoBot, todos os 4 bots especializados serão 
              automaticamente desativados. O UnicoBot assumirá controle total usando a Smart Strategy.
            </div>
          </div>
        )}
      </div>

      {/* Bots Especializados */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Bot className="w-5 h-5" />
          Bots Especializados
          {uniBot?.enabled && (
            <span className="text-sm text-gray-500 font-normal">(desativados - UnicoBot ativo)</span>
          )}
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bots.map((bot) => (
            <div 
              key={bot.bot_type}
              className={`p-5 rounded-xl border transition ${
                bot.enabled && !uniBot?.enabled
                  ? 'bg-dark-100 border-green-500/50'
                  : 'bg-dark-100/50 border-gray-700 opacity-75'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    bot.enabled && !uniBot?.enabled ? 'bg-green-500/20' : 'bg-gray-700'
                  }`}>
                    <Bot className={`w-6 h-6 ${
                      bot.enabled && !uniBot?.enabled ? 'text-green-400' : 'text-gray-500'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white">{bot.name}</h4>
                    <p className="text-xs text-gray-500">{bot.bot_type}</p>
                  </div>
                </div>
                
                <button
                  onClick={() => toggleBot(bot.bot_type, !bot.enabled)}
                  disabled={actionLoading === bot.bot_type || uniBot?.enabled}
                  className={`p-2 rounded-lg transition ${
                    bot.enabled
                      ? 'bg-green-500/20 hover:bg-green-500/30 text-green-400'
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-400'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={uniBot?.enabled ? 'Desative o UnicoBot primeiro' : (bot.enabled ? 'Pausar bot' : 'Ativar bot')}
                >
                  {actionLoading === bot.bot_type ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : bot.enabled ? (
                    <Power className="w-5 h-5" />
                  ) : (
                    <PowerOff className="w-5 h-5" />
                  )}
                </button>
              </div>
              
              <div className="mt-4 grid grid-cols-3 gap-3">
                <div>
                  <p className="text-xs text-gray-500">Win Rate</p>
                  <p className={`font-medium ${
                    bot.win_rate >= 50 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {bot.win_rate.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Trades</p>
                  <p className="font-medium text-white">{bot.total_trades}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">PnL Hoje</p>
                  <p className={`font-medium ${
                    bot.pnl_today >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    ${bot.pnl_today.toFixed(2)}
                  </p>
                </div>
              </div>
              
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className={`px-2 py-0.5 rounded text-xs ${
                  bot.enabled && !uniBot?.enabled
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {uniBot?.enabled ? 'Pausado (UnicoBot ativo)' : (bot.enabled ? 'Ativo' : 'Pausado')}
                </span>
                <span className="text-gray-500">
                  {bot.open_positions} posições abertas
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Info Card */}
      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-sm text-blue-200">
            <strong>Dica:</strong> Você pode pausar bots com baixo desempenho e redistribuir capital para os melhores.
            O UnicoBot é recomendado para gerenciamento simplificado com a Smart Strategy otimizada.
          </div>
        </div>
      </div>
    </div>
  )
}
