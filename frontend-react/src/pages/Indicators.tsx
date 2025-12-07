import { useEffect, useState, useCallback } from 'react'
import { Activity, TrendingUp, TrendingDown, Minus, RefreshCw, Bot } from 'lucide-react'
import { dashboardApi } from '../services/api'

interface CryptoIndicator {
  symbol: string
  price: number
  rsi: number
  macd: number
  macd_signal: number
  trend: 'ALTA' | 'QUEDA' | 'LATERAL'
  trend_strength: number
  sma20: number
  ema9: number
  ema21: number
  volume_ratio: number
  buy_signal: boolean
  sell_signal: boolean
  bot_assigned: string | null
}

interface BotIndicatorConfig {
  name: string
  speed_profile: string
  strategy_type: string
  symbols: string[]
  buy_conditions: string
  sell_conditions: string
}

export default function Indicators() {
  const [indicators, setIndicators] = useState<CryptoIndicator[]>([])
  const [botsConfig, setBotsConfig] = useState<BotIndicatorConfig[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchIndicators = useCallback(async () => {
    try {
      const response = await dashboardApi.getIndicators()
      setIndicators(response.data.indicators || [])
      setBotsConfig(response.data.bots_config || [])
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Erro ao carregar indicadores:', error)
      // Dados mock para demonstração
      setIndicators([
        {
          symbol: 'BTCUSDT',
          price: 43250.50,
          rsi: 42,
          macd: 125.5,
          macd_signal: 118.2,
          trend: 'ALTA',
          trend_strength: 3,
          sma20: 43100,
          ema9: 43180,
          ema21: 43050,
          volume_ratio: 1.2,
          buy_signal: true,
          sell_signal: false,
          bot_assigned: 'Bot Estável'
        },
        {
          symbol: 'ETHUSDT',
          price: 2285.30,
          rsi: 55,
          macd: 12.3,
          macd_signal: 10.8,
          trend: 'LATERAL',
          trend_strength: 2,
          sma20: 2280,
          ema9: 2282,
          ema21: 2275,
          volume_ratio: 0.9,
          buy_signal: false,
          sell_signal: false,
          bot_assigned: 'Bot Estável'
        },
        {
          symbol: 'SOLUSDT',
          price: 98.45,
          rsi: 38,
          macd: -0.8,
          macd_signal: -1.2,
          trend: 'LATERAL',
          trend_strength: 2,
          sma20: 99.2,
          ema9: 98.1,
          ema21: 98.8,
          volume_ratio: 1.4,
          buy_signal: true,
          sell_signal: false,
          bot_assigned: 'Bot Médio'
        },
        {
          symbol: 'XRPUSDT',
          price: 0.5230,
          rsi: 68,
          macd: 0.012,
          macd_signal: 0.015,
          trend: 'QUEDA',
          trend_strength: 3,
          sma20: 0.525,
          ema9: 0.522,
          ema21: 0.524,
          volume_ratio: 0.8,
          buy_signal: false,
          sell_signal: true,
          bot_assigned: 'Bot Volátil'
        },
        {
          symbol: 'DOGEUSDT',
          price: 0.0825,
          rsi: 72,
          macd: 0.0008,
          macd_signal: 0.0005,
          trend: 'ALTA',
          trend_strength: 4,
          sma20: 0.0812,
          ema9: 0.0820,
          ema21: 0.0815,
          volume_ratio: 2.1,
          buy_signal: false,
          sell_signal: true,
          bot_assigned: 'Bot Meme (Scalper)'
        }
      ])
      setBotsConfig([
        { name: 'Bot Estável', speed_profile: 'slow', strategy_type: 'holder', symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'LTCUSDT'], buy_conditions: 'all', sell_conditions: 'any' },
        { name: 'Bot Médio', speed_profile: 'medium', strategy_type: 'swing', symbols: ['SOLUSDT', 'LINKUSDT', 'AVAXUSDT', 'DOTUSDT', 'NEARUSDT'], buy_conditions: 'majority', sell_conditions: 'majority' },
        { name: 'Bot Volátil', speed_profile: 'fast', strategy_type: 'momentum', symbols: ['XRPUSDT', 'ADAUSDT', 'TRXUSDT'], buy_conditions: 'any', sell_conditions: 'any' },
        { name: 'Bot Meme (Scalper)', speed_profile: 'ultra_fast', strategy_type: 'scalper', symbols: ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT'], buy_conditions: 'instant', sell_conditions: 'instant' }
      ])
      setLastUpdate(new Date())
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchIndicators()

    if (autoRefresh) {
      const interval = setInterval(fetchIndicators, 10000) // 10 segundos
      return () => clearInterval(interval)
    }
  }, [fetchIndicators, autoRefresh])

  const getRSIColor = (rsi: number) => {
    if (rsi < 30) return 'text-green-400 bg-green-500/10'
    if (rsi < 40) return 'text-green-300 bg-green-500/5'
    if (rsi > 70) return 'text-red-400 bg-red-500/10'
    if (rsi > 60) return 'text-red-300 bg-red-500/5'
    return 'text-gray-300 bg-gray-500/10'
  }

  const getRSILabel = (rsi: number) => {
    if (rsi < 30) return 'Oversold 🟢'
    if (rsi < 40) return 'Baixo'
    if (rsi > 70) return 'Overbought 🔴'
    if (rsi > 60) return 'Alto'
    return 'Neutro'
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'ALTA':
        return <TrendingUp className="w-4 h-4 text-green-400" />
      case 'QUEDA':
        return <TrendingDown className="w-4 h-4 text-red-400" />
      default:
        return <Minus className="w-4 h-4 text-gray-400" />
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'ALTA':
        return 'text-green-400 bg-green-500/10'
      case 'QUEDA':
        return 'text-red-400 bg-red-500/10'
      default:
        return 'text-yellow-400 bg-yellow-500/10'
    }
  }

  const getSpeedBadge = (speed: string) => {
    const colors: Record<string, string> = {
      slow: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      fast: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      ultra_fast: 'bg-red-500/20 text-red-400 border-red-500/30'
    }
    const labels: Record<string, string> = {
      slow: '🐢 Lento',
      medium: '⚖️ Médio',
      fast: '⚡ Rápido',
      ultra_fast: '🚀 Ultra-Rápido'
    }
    return (
      <span className={`px-2 py-1 rounded text-xs border ${colors[speed] || 'bg-gray-500/20'}`}>
        {labels[speed] || speed}
      </span>
    )
  }

  const getConditionsBadge = (conditions: string) => {
    const labels: Record<string, { text: string; color: string }> = {
      all: { text: 'TODOS indicadores', color: 'bg-blue-500/20 text-blue-300' },
      majority: { text: '2/3 indicadores', color: 'bg-yellow-500/20 text-yellow-300' },
      any: { text: 'QUALQUER indicador', color: 'bg-orange-500/20 text-orange-300' },
      instant: { text: 'INSTANTÂNEO', color: 'bg-red-500/20 text-red-300' }
    }
    const config = labels[conditions] || { text: conditions, color: 'bg-gray-500/20' }
    return (
      <span className={`px-2 py-0.5 rounded text-xs ${config.color}`}>
        {config.text}
      </span>
    )
  }

  const getMACDStatus = (macd: number, signal: number) => {
    if (macd > signal) {
      return { text: 'Bullish ↑', color: 'text-green-400' }
    } else if (macd < signal) {
      return { text: 'Bearish ↓', color: 'text-red-400' }
    }
    return { text: 'Neutro', color: 'text-gray-400' }
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">📊 Indicadores por Moeda</h1>
          <p className="text-sm text-gray-400 mt-1">
            Análise técnica em tempo real - RSI, MACD, Tendência
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded bg-dark-700 border-gray-600"
            />
            Auto-refresh
          </label>
          <button
            onClick={fetchIndicators}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </button>
        </div>
      </div>

      {lastUpdate && (
        <p className="text-xs text-gray-500">
          Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
        </p>
      )}

      {/* Estratégia dos Bots */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary-400" />
          Estratégias por Bot
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {botsConfig.map((bot) => (
            <div key={bot.name} className="bg-dark-700 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-white">{bot.name}</h3>
                {getSpeedBadge(bot.speed_profile)}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Tipo:</span>
                  <span className="text-gray-200 capitalize">{bot.strategy_type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Compra:</span>
                  {getConditionsBadge(bot.buy_conditions)}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Venda:</span>
                  {getConditionsBadge(bot.sell_conditions)}
                </div>
                <div className="mt-2 pt-2 border-t border-gray-600">
                  <span className="text-gray-400 text-xs">Moedas: </span>
                  <span className="text-gray-300 text-xs">
                    {bot.symbols.slice(0, 3).join(', ')}
                    {bot.symbols.length > 3 && ` +${bot.symbols.length - 3}`}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legenda de Indicadores */}
      <div className="card bg-dark-800/50">
        <h3 className="text-sm font-medium text-gray-300 mb-3">📖 Legenda dos Sinais</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-400">RSI {'<'} 30:</span>
            <span className="text-green-400 ml-2">🟢 COMPRA (Oversold)</span>
          </div>
          <div>
            <span className="text-gray-400">RSI {'>'} 70:</span>
            <span className="text-red-400 ml-2">🔴 VENDA (Overbought)</span>
          </div>
          <div>
            <span className="text-gray-400">MACD {'>'} Sinal:</span>
            <span className="text-green-400 ml-2">↑ Bullish</span>
          </div>
          <div>
            <span className="text-gray-400">MACD {'<'} Sinal:</span>
            <span className="text-red-400 ml-2">↓ Bearish</span>
          </div>
        </div>
      </div>

      {/* Tabela de Indicadores */}
      <div className="card overflow-x-auto">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary-400" />
          Indicadores em Tempo Real
        </h2>
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
              <th className="pb-3 pr-4">Moeda</th>
              <th className="pb-3 pr-4">Preço</th>
              <th className="pb-3 pr-4">RSI</th>
              <th className="pb-3 pr-4">MACD</th>
              <th className="pb-3 pr-4">Tendência</th>
              <th className="pb-3 pr-4">Volume</th>
              <th className="pb-3 pr-4">Sinal</th>
              <th className="pb-3">Bot</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((crypto) => {
              const macdStatus = getMACDStatus(crypto.macd, crypto.macd_signal)
              return (
                <tr key={crypto.symbol} className="border-b border-gray-700/50 hover:bg-dark-700/50">
                  <td className="py-3 pr-4">
                    <span className="font-medium text-white">{crypto.symbol.replace('USDT', '')}</span>
                    <span className="text-gray-500 text-sm">/USDT</span>
                  </td>
                  <td className="py-3 pr-4 text-gray-200">
                    ${crypto.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: crypto.price < 1 ? 4 : 2 })}
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-sm font-medium ${getRSIColor(crypto.rsi)}`}>
                        {crypto.rsi.toFixed(1)}
                      </span>
                      <span className="text-xs text-gray-400">{getRSILabel(crypto.rsi)}</span>
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex flex-col">
                      <span className={`text-sm ${macdStatus.color}`}>{macdStatus.text}</span>
                      <span className="text-xs text-gray-500">
                        {crypto.macd > 0 ? '+' : ''}{crypto.macd.toFixed(4)}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-sm flex items-center gap-1 ${getTrendColor(crypto.trend)}`}>
                        {getTrendIcon(crypto.trend)}
                        {crypto.trend}
                      </span>
                      <span className="text-xs text-gray-500">
                        {crypto.trend_strength}/4
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={`text-sm ${crypto.volume_ratio > 1.5 ? 'text-green-400' : crypto.volume_ratio < 0.7 ? 'text-red-400' : 'text-gray-300'}`}>
                      {crypto.volume_ratio.toFixed(1)}x
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    {crypto.buy_signal && (
                      <span className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400 border border-green-500/30">
                        🟢 COMPRA
                      </span>
                    )}
                    {crypto.sell_signal && (
                      <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400 border border-red-500/30">
                        🔴 VENDA
                      </span>
                    )}
                    {!crypto.buy_signal && !crypto.sell_signal && (
                      <span className="px-2 py-1 rounded text-xs bg-gray-500/20 text-gray-400">
                        ⏸️ AGUARDAR
                      </span>
                    )}
                  </td>
                  <td className="py-3">
                    <span className="text-xs text-gray-400">
                      {crypto.bot_assigned || '-'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Explicação das Estratégias */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-medium text-white mb-3">🟢 Condições de COMPRA</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-green-400">•</span>
              <span><strong>RSI Baixo:</strong> RSI abaixo do threshold (varia por bot)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">•</span>
              <span><strong>MACD Cruzando:</strong> MACD cruzou acima do sinal</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">•</span>
              <span><strong>Tendência:</strong> Não pode estar em QUEDA forte</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">•</span>
              <span><strong>Preço:</strong> Próximo ou abaixo da SMA20 (suporte)</span>
            </li>
          </ul>
        </div>
        <div className="card">
          <h3 className="font-medium text-white mb-3">🔴 Condições de VENDA</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-red-400">•</span>
              <span><strong>RSI Alto:</strong> RSI acima do threshold (overbought)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-400">•</span>
              <span><strong>MACD Cruzando:</strong> MACD cruzou abaixo do sinal</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-400">•</span>
              <span><strong>Tendência:</strong> Mudou de ALTA para LATERAL/QUEDA</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-400">•</span>
              <span><strong>Stop/Take:</strong> Atingiu stop loss ou take profit</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
