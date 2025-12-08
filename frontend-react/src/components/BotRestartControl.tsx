import { useState } from 'react'
import { RotateCw, AlertTriangle, Check } from 'lucide-react'

interface BotControlProps {
  botType: string
  botName: string
  isEnabled: boolean
  onRefresh?: () => void
}

interface RestartResponse {
  success: boolean
  message?: string
  error?: string
}

export default function BotRestartControl({ botType, botName, isEnabled, onRefresh }: BotControlProps) {
  const [isRestarting, setIsRestarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)
  const [lastAction, setLastAction] = useState<string | null>(null)

  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 4000)
  }

  const handleRestart = async () => {
    if (!confirm(`Tem certeza que deseja reiniciar ${botName}? As posições abertas serão preservadas.`)) {
      return
    }

    setIsRestarting(true)
    try {
      const response = await fetch('/api/actions/restart-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          bot_type: botType,
          reason: 'manual_restart_ui'
        })
      })

      const data: RestartResponse = await response.json()

      if (data.success) {
        showMessage('success', `${botName} está sendo reiniciado...`)
        setLastAction(`Reinício iniciado em ${new Date().toLocaleTimeString()}`)
        if (onRefresh) setTimeout(onRefresh, 2000)
      } else {
        showMessage('error', data.error || 'Erro ao reiniciar bot')
      }
    } catch (error) {
      showMessage('error', `Erro ao reiniciar: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setIsRestarting(false)
    }
  }

  const handleStop = async () => {
    if (!confirm(`Tem certeza que deseja parar ${botName}?`)) {
      return
    }

    setIsStopping(true)
    try {
      const response = await fetch('/api/actions/stop-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          bot_type: botType,
          reason: 'manual_stop_ui'
        })
      })

      const data: RestartResponse = await response.json()

      if (data.success) {
        showMessage('success', `${botName} foi parado`)
        setLastAction(`Parada executada em ${new Date().toLocaleTimeString()}`)
        if (onRefresh) setTimeout(onRefresh, 2000)
      } else {
        showMessage('error', data.error || 'Erro ao parar bot')
      }
    } catch (error) {
      showMessage('error', `Erro ao parar: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setIsStopping(false)
    }
  }

  const handleRestartAll = async () => {
    if (!confirm('Tem certeza que deseja reiniciar TODOS os bots? As posições serão preservadas.')) {
      return
    }

    setIsRestarting(true)
    try {
      const response = await fetch('/api/actions/restart-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          reason: 'manual_restart_all_ui'
        })
      })

      const data: RestartResponse = await response.json()

      if (data.success) {
        showMessage('success', 'Todos os bots estão sendo reiniciados...')
        setLastAction(`Reinício geral iniciado em ${new Date().toLocaleTimeString()}`)
        if (onRefresh) setTimeout(onRefresh, 3000)
      } else {
        showMessage('error', data.error || 'Erro ao reiniciar bots')
      }
    } catch (error) {
      showMessage('error', `Erro ao reiniciar: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setIsRestarting(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Status e mensagens */}
      {message && (
        <div className={`p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-300'
            : message.type === 'error'
            ? 'bg-red-100 text-red-800 border border-red-300'
            : 'bg-blue-100 text-blue-800 border border-blue-300'
        }`}>
          {message.type === 'success' && <Check size={18} />}
          {message.type === 'error' && <AlertTriangle size={18} />}
          {message.text}
        </div>
      )}

      {lastAction && (
        <div className="text-sm text-gray-600 border-l-2 border-gray-300 pl-3 py-2">
          {lastAction}
        </div>
      )}

      {/* Controles */}
      <div className="space-y-3">
        {/* Restart individual */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-blue-900 flex items-center gap-2">
                <RotateCw size={16} />
                Reiniciar {botName}
              </h4>
              <p className="text-sm text-blue-700 mt-1">
                Reinicia o bot com nova configuração. Posições serão preservadas.
              </p>
            </div>
            <button
              onClick={handleRestart}
              disabled={isRestarting || !isEnabled}
              className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition ${
                isEnabled
                  ? 'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isRestarting && <RotateCw size={16} className="animate-spin" />}
              {isRestarting ? 'Reiniciando...' : 'Reiniciar'}
            </button>
          </div>
        </div>

        {/* Stop */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-yellow-900">Parar {botName}</h4>
              <p className="text-sm text-yellow-700 mt-1">
                Desativa o bot. Posições abertas permanecerão.
              </p>
            </div>
            <button
              onClick={handleStop}
              disabled={isStopping || !isEnabled}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                isEnabled
                  ? 'bg-yellow-600 hover:bg-yellow-700 text-white disabled:opacity-50'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isStopping ? 'Parando...' : 'Parar'}
            </button>
          </div>
        </div>

        {/* Restart all - apenas se for o primeiro bot ou em uma seção separada */}
        {botType === 'bot_estavel' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-red-900 flex items-center gap-2">
                  <AlertTriangle size={16} />
                  Reiniciar TODOS os bots
                </h4>
                <p className="text-sm text-red-700 mt-1">
                  Reinicia todos os 4 bots com nova configuração. Posições serão preservadas.
                </p>
              </div>
              <button
                onClick={handleRestartAll}
                disabled={isRestarting}
                className="px-4 py-2 rounded-lg font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 transition"
              >
                {isRestarting ? 'Reiniciando...' : 'Reiniciar Todos'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700">
        <strong>ℹ️ Dica:</strong> Use os botões de reinício após alterar configurações sensíveis
        (risco, RSI, take-profit). As posições abertas serão automaticamente preservadas.
      </div>
    </div>
  )
}
