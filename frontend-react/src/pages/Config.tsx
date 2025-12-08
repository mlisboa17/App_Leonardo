import { useEffect, useState } from 'react'
import { configApi } from '../services/api'
import { Save, Bot, Settings, AlertTriangle } from 'lucide-react'

interface BotConfig {
  name: string
  enabled: boolean
  amount_per_trade: number
  take_profit: number
  take_profit_dinamico?: Record<string, number>
    rsi_dinamico?: Record<string, { compra: number; venda: number }>
  stop_loss: number
  trailing_stop?: string
  max_positions: number
  rsi_compra?: number
  rsi_venda?: number
  perfil?: string
  extras?: string[]
  symbols: string[]
}

export default function Config() {
  const [bots, setBots] = useState<Record<string, BotConfig>>({})
  const [globalConfig, setGlobalConfig] = useState<Record<string, unknown>>({})
  const profileOptions = [
    { label: 'Conservador', value: 'conservador' },
    { label: 'Normal', value: 'normal' },
    { label: 'Agressivo', value: 'agressivo' },
  ]
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)

  const fetchConfig = async () => {
    try {
      const [botsResponse, globalResponse] = await Promise.all([
        configApi.getBots(),
        configApi.getGlobal(),
      ])
      // Coerce nested dynamic mappings to number types where applicable
      const rawBots = botsResponse.data || {}
      const coercedBots: Record<string, BotConfig> = {}
      Object.entries(rawBots).forEach(([key, b]) => {
        const bot = { ...(b as BotConfig) } as any
        if (bot.take_profit_dinamico) {
          const coerced: Record<string, number> = {}
          Object.entries(bot.take_profit_dinamico).forEach(([k, v]) => {
            coerced[k] = Number(String(v).replace('%', '').trim())
          })
          bot.take_profit_dinamico = coerced
        }
        if (bot.rsi_dinamico) {
          const coercedRsi: Record<string, { compra: number; venda: number }> = {}
          Object.entries(bot.rsi_dinamico).forEach(([k, v]) => {
            const compra = Number((v as any)?.compra || (v as any))
            const venda = Number((v as any)?.venda || (v as any))
            coercedRsi[k] = { compra: Number(compra), venda: Number(venda) }
          })
          bot.rsi_dinamico = coercedRsi
        }
        coercedBots[key] = bot
      })
      setBots(coercedBots)
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

  const handleBotUpdate = (name: string, key: string, value: unknown) => {
    setBots(prev => ({
      ...prev,
      [name]: { ...prev[name], [key]: value }
    }))
  }

  const handleBotNestedUpdate = (name: string, field: string, subKey: string | number, value: unknown) => {
    setBots(prev => {
      const bot = prev[name] || {}
      const nested = { ...(((bot as any)[field] as Record<string, any>) || {}) }
      nested[subKey as any] = value
      return {
        ...prev,
        [name]: { ...bot, [field]: nested }
      }
    })
  }

  const handleDeleteNested = (name: string, field: string, subKey: string | number) => {
    setBots(prev => {
      const bot = prev[name] || {}
      const nested = { ...(((bot as any)[field] as Record<string, any>) || {}) }
      delete nested[subKey as any]
      return {
        ...prev,
        [name]: { ...bot, [field]: nested }
      }
    })
  }

  const handleAddTakeProfitRow = (name: string) => {
    // nova entrada em minutos (ex: 10)
    const defaultKey = '10'
    setBots(prev => {
      const bot = prev[name] || {}
      const nested = { ...(((bot as any)['take_profit_dinamico'] as Record<string, any>) || {}) }
      let key = defaultKey
      let i = 1
      while (nested[key]) {
        key = `${parseInt(defaultKey) * ++i}`
      }
      nested[key] = 1.0
      return { ...prev, [name]: { ...bot, take_profit_dinamico: nested } }
    })
  }

  const handleAddRsiRow = (name: string) => {
    const defaultKey = '10'
    setBots(prev => {
      const bot = prev[name] || {}
      const nested = { ...(((bot as any)['rsi_dinamico'] as Record<string, any>) || {}) }
      let key = defaultKey
      let i = 1
      while (nested[key]) {
        key = `${parseInt(defaultKey) * ++i}`
      }
      nested[key] = { compra: 40, venda: 65 }
      return { ...prev, [name]: { ...bot, rsi_dinamico: nested } }
    })
  }

  // Novas configurações detalhadas dos bots (padrões fornecidos)
  type BotProfileConfig = {
    perfil: string
    take_profit_dinamico: Record<string, number>
    rsi: { compra: number; venda: number }
    trailing_stop: string
    extras: string[]
  }
  type BotProfilesType = {
    [botKey: string]: BotProfileConfig
  }
  const botProfiles: BotProfilesType = {
    bot_estavel: {
      perfil: 'Conservador, moedas fortes (BTC, ETH, BNB, LTC)',
      take_profit_dinamico: { inicio: 2.5, '60min': 1.5, '120min': 1.0 },
      rsi: { compra: 40, venda: 70 },
      trailing_stop: '0.3-0.4%',
      extras: [
        'Permitir compra com 70% dos indicadores positivos',
        'TP e SL baseados em volatilidade (ATR)',
        'Lucros pequenos e constantes',
      ],
    },
    bot_medio: {
      perfil: 'Oscilações médias (SOL, LINK, AVAX, DOT, NEAR)',
      take_profit_dinamico: { inicio: 3.0, '30min': 2.0, '90min': 1.5 },
      rsi: { compra: 45, venda: 65 },
      trailing_stop: '0.4-0.5%',
      extras: [
        'Vender metade em 2% e deixar resto correr com trailing',
        'Confirmar entradas com volume',
        'TP variável por amplitude (Bollinger/ATR)',
      ],
    },
    bot_volatil: {
      perfil: 'Moedas de alta oscilação (XRP, ADA, TRX)',
      take_profit_dinamico: { inicio: 2.0, '20min': 1.5, '60min': 1.0 },
      rsi: { compra: 50, venda: 75 },
      trailing_stop: '0.5-0.7%',
      extras: [
        'Filtro de volume mínimo para evitar falsas entradas',
        'Operar em horários de maior liquidez',
        'Saídas rápidas ao menor sinal de reversão',
      ],
    },
    bot_meme: {
      perfil: 'Ultra-rápido (DOGE, SHIB, PEPE)',
      take_profit_dinamico: { inicio: 1.2, '10min': 0.8, '20min': 0.5 },
      rsi: { compra: 55, venda: 65 },
      trailing_stop: '0.2-0.3%',
      extras: [
        'Limitar máximo de 10 trades/hora',
        'Incluir taxas/spread no cálculo do lucro mínimo',
        'Só operar em momentos de alta volatilidade confirmada',
      ],
    },
  }

  // Aplica esses padrões a cada bot na UI (mapeamento -> estado `bots`)
  const handleApplyDefaults = () => {
    const newBots = { ...bots }
    const parsePercent = (s: string | number) => {
      if (typeof s === 'number') return s
      return parseFloat((s || '').toString().replace('%', '').replace(/[^0-9.-]/g, '')) || 0
    }
    const parseRsiNumber = (rsiStr: string | number) => {
      if (typeof rsiStr === 'number') return rsiStr
      if (!rsiStr) return 0
      const match = (rsiStr as string).match(/(\d{1,3})/)
      return match ? parseInt(match[1], 10) : 0
    }

    Object.entries(botProfiles).forEach(([botKey, profile]) => {
      if (newBots[botKey]) {
        newBots[botKey] = {
          ...newBots[botKey],
          perfil: profile.perfil,
          take_profit: parsePercent(profile.take_profit_dinamico.inicio),
          take_profit_dinamico: profile.take_profit_dinamico,
          rsi_compra: parseRsiNumber(profile.rsi.compra),
          rsi_venda: parseRsiNumber(profile.rsi.venda),
          trailing_stop: profile.trailing_stop,
          extras: profile.extras,
        }
      }
    })
    setBots(newBots)
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage(null)
    
    try {
      let restarts = 0
      for (const [name, config] of Object.entries(bots)) {
        const resp = await configApi.updateBot(name, config as unknown as Record<string, unknown>)
        if (resp?.data?.data?.restart_scheduled || resp?.data?.restart_scheduled) restarts += 1
      }
      const globalResp = await configApi.updateGlobal(globalConfig)
      if (globalResp?.data?.data?.restart_scheduled || globalResp?.data?.restart_scheduled) restarts += 1
      setMessage({ type: 'success', text: `Configurações salvas com sucesso! ${restarts > 0 ? `Reinício agendado para ${restarts} item(s).` : 'Nenhum reinício necessário.'}` })
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao salvar configurações' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleToggleBot = async (name: string) => {
    try {
      const bot = bots[name]
      let resp
      if (bot.enabled) {
        resp = await configApi.disableBot(name)
      } else {
        resp = await configApi.enableBot(name)
      }
      const restart = resp?.data?.data?.restart_scheduled || resp?.data?.restart_scheduled

      if (restart) {
        setMessage({ type: 'info', text: 'Alteração salva — reinício agendado para aplicar mudanças.' })
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
        <div className="flex gap-2">
          <button
            onClick={handleApplyDefaults}
            className="btn btn-secondary flex items-center gap-2"
          >
            Aplicar Padrões
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn btn-primary flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : message.type === 'info' ? 'bg-blue-500/10 border border-blue-500/30 text-blue-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Perfil de Risco</label>
            <select
              className="input"
              value={globalConfig.profile as string || 'normal'}
              onChange={e => setGlobalConfig(prev => ({ ...prev, profile: e.target.value }))}
            >
              {profileOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
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
            <div className="mt-3 flex flex-col gap-2">
              <div className="text-sm text-gray-400">Perfil: <span className="text-white ml-2">{config.perfil || '-'}</span></div>
              <div className="text-sm text-gray-400">Trailing Stop: <span className="text-white ml-2">{config.trailing_stop || '-'}</span></div>
              {config.take_profit_dinamico && (
                <div className="text-sm text-gray-400">Take Profit Dinâmico:
                  <ul className="list-disc ml-6 text-gray-300">
                    {Object.entries(config.take_profit_dinamico).map(([k, v]) => (
                      <li key={k} className="text-xs">{k}: {v}</li>
                    ))}
                  </ul>
                </div>
              )}
              {config.extras && config.extras.length > 0 && (
                <div className="text-sm text-gray-400">Extras:
                  <ul className="list-disc ml-6 text-gray-300">
                    {config.extras.map((ex, i) => (
                      <li key={i} className="text-xs">{ex}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Stop Loss (%)</label>
                <input
                  type="number"
                  value={config.stop_loss || 0}
                  onChange={e => handleBotUpdate(name, 'stop_loss', parseFloat(e.target.value))}
                  className="input"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Take Profit (%)</label>
                <input
                  type="number"
                  value={config.take_profit || 0}
                  onChange={e => handleBotUpdate(name, 'take_profit', parseFloat(e.target.value))}
                  className="input"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">RSI Compra</label>
                <input
                  type="number"
                  value={config.rsi_compra || 0}
                  onChange={e => handleBotUpdate(name, 'rsi_compra', parseFloat(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">RSI Venda</label>
                <input
                  type="number"
                  value={config.rsi_venda || 0}
                  onChange={e => handleBotUpdate(name, 'rsi_venda', parseFloat(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Max Posições</label>
                <input
                  type="number"
                  value={config.max_positions || 0}
                  onChange={e => handleBotUpdate(name, 'max_positions', parseInt(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Valor por Trade ($)</label>
                <input
                  type="number"
                  value={config.amount_per_trade || 0}
                  onChange={e => handleBotUpdate(name, 'amount_per_trade', parseFloat(e.target.value))}
                  className="input"
                  step="1"
                />
              </div>
            </div>
            <details className="mt-4 p-3 border rounded-lg border-gray-700/40 bg-dark-700/50">
              <summary className="cursor-pointer font-medium text-white">Dinâmicos (Take Profit / RSI)</summary>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm text-gray-200 mb-2">Take Profit Dinâmico</h4>
                  <div className="space-y-2">
                    {config.take_profit_dinamico && Object.entries(config.take_profit_dinamico as Record<string, number>).map(([k, v]) => (
                      <div key={k} className="flex gap-2 items-center">
                        <input value={k} readOnly className="input input-sm w-20" />
                        <input
                          type="number"
                          step="0.1"
                          className="input input-sm"
                          value={Number(v)}
                          onChange={(e) => handleBotNestedUpdate(name, 'take_profit_dinamico', k, parseFloat(e.target.value))}
                        />
                        <span className="text-gray-400">%</span>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteNested(name, 'take_profit_dinamico', k)}>Remover</button>
                      </div>
                    ))}
                    <div>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleAddTakeProfitRow(name)}>Adicionar TP</button>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm text-gray-200 mb-2">RSI Dinâmico (compra/venda)</h4>
                  <div className="space-y-2">
                    {config.rsi_dinamico && Object.entries(config.rsi_dinamico).map(([k, v]) => (
                      <div key={k} className="flex gap-2 items-center">
                        <input value={k} readOnly className="input input-sm w-20" />
                        <input
                          type="number"
                          step="1"
                          className="input input-sm w-20"
                          value={(v as any).compra}
                          onChange={(e) => handleBotNestedUpdate(name, 'rsi_dinamico', k, { ...(v as any), compra: parseInt(e.target.value) })}
                        />
                        <input
                          type="number"
                          step="1"
                          className="input input-sm w-20"
                          value={(v as any).venda}
                          onChange={(e) => handleBotNestedUpdate(name, 'rsi_dinamico', k, { ...(v as any), venda: parseInt(e.target.value) })}
                        />
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteNested(name, 'rsi_dinamico', k)}>Remover</button>
                      </div>
                    ))}
                    <div>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleAddRsiRow(name)}>Adicionar RSI</button>
                    </div>
                  </div>
                </div>
              </div>
            </details>
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
