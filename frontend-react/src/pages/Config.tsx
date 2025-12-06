import { useEffect, useState } from 'react'
import { configApi } from '../services/api'
import { Save, Bot, Settings, AlertTriangle } from 'lucide-react'

interface BotConfig {
  name: string
  enabled: boolean
  amount_per_trade: number
  take_profit: number
  stop_loss: number
  max_positions: number
  symbols: string[]
}

export default function Config() {
  const [bots, setBots] = useState<Record<string, BotConfig>>({})
  const [globalConfig, setGlobalConfig] = useState<Record<string, unknown>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const fetchConfig = async () => {
    try {
      const [botsResponse, globalResponse] = await Promise.all([
        configApi.getBots(),
        configApi.getGlobal(),
      ])
      setBots(botsResponse.data || {})
      setGlobalConfig(globalResponse.data || {})
    } catch (error) {
      console.error('Erro ao carregar configurações:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const handleBotUpdate = async (name: string, key: string, value: unknown) => {
    setBots(prev => ({
      ...prev,
      [name]: { ...prev[name], [key]: value }
    }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage(null)
    
    try {
      for (const [name, config] of Object.entries(bots)) {
        await configApi.updateBot(name, config as Record<string, unknown>)
      }
      await configApi.updateGlobal(globalConfig)
      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao salvar configurações' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleToggleBot = async (name: string) => {
    try {
      const bot = bots[name]
      if (bot.enabled) {
        await configApi.disableBot(name)
      } else {
        await configApi.enableBot(name)
      }
      setBots(prev => ({
        ...prev,
        [name]: { ...prev[name], enabled: !prev[name].enabled }
      }))
    } catch (error) {
      console.error('Erro ao alterar status do bot:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Configurações</h1>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn btn-primary flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {isSaving ? 'Salvando...' : 'Salvar Alterações'}
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
          {message.text}
        </div>
      )}

      {/* Global Config */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Settings className="w-5 h-5 text-purple-400" />
          </div>
          <h2 className="text-lg font-semibold text-white">Configurações Globais</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Meta Mensal (%)</label>
            <input
              type="number"
              value={globalConfig.monthly_target as number || 0}
              onChange={(e) => setGlobalConfig(prev => ({ ...prev, monthly_target: parseFloat(e.target.value) }))}
              className="input"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Risco por Trade (%)</label>
            <input
              type="number"
              value={globalConfig.risk_per_trade as number || 0}
              onChange={(e) => setGlobalConfig(prev => ({ ...prev, risk_per_trade: parseFloat(e.target.value) }))}
              className="input"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Max Loss Diário (%)</label>
            <input
              type="number"
              value={globalConfig.max_daily_loss as number || 0}
              onChange={(e) => setGlobalConfig(prev => ({ ...prev, max_daily_loss: parseFloat(e.target.value) }))}
              className="input"
              step="0.1"
            />
          </div>
        </div>
      </div>

      {/* Bot Configs */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Bot className="w-5 h-5" />
          Configurações dos Bots
        </h2>

        {Object.entries(bots).map(([name, config]) => (
          <div key={name} className="card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${config.enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                <h3 className="text-lg font-semibold text-white capitalize">{name}</h3>
              </div>
              <button
                onClick={() => handleToggleBot(name)}
                className={`btn ${config.enabled ? 'btn-danger' : 'btn-primary'}`}
              >
                {config.enabled ? 'Desabilitar' : 'Habilitar'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Valor por Trade ($)</label>
                <input
                  type="number"
                  value={config.amount_per_trade || 0}
                  onChange={(e) => handleBotUpdate(name, 'amount_per_trade', parseFloat(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Take Profit (%)</label>
                <input
                  type="number"
                  value={config.take_profit || 0}
                  onChange={(e) => handleBotUpdate(name, 'take_profit', parseFloat(e.target.value))}
                  className="input"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Stop Loss (%)</label>
                <input
                  type="number"
                  value={config.stop_loss || 0}
                  onChange={(e) => handleBotUpdate(name, 'stop_loss', parseFloat(e.target.value))}
                  className="input"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Max Posições</label>
                <input
                  type="number"
                  value={config.max_positions || 0}
                  onChange={(e) => handleBotUpdate(name, 'max_positions', parseInt(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Warning */}
      <div className="card bg-yellow-500/5 border-yellow-500/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-yellow-400">Atenção</h3>
            <p className="text-sm text-gray-400 mt-1">
              Alterações nas configurações podem afetar trades em andamento. 
              Certifique-se de entender o impacto antes de salvar.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
