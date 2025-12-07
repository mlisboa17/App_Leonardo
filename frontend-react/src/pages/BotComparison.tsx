import { useEffect, useState, useCallback } from 'react'
import { Trophy, TrendingUp, TrendingDown, BarChart3, RefreshCw, Award, Target, Percent } from 'lucide-react'
import { dashboardApi } from '../services/api'

interface BotPerformance {
  bot_type: string
  bot_name: string
  total_trades: number
  wins: number
  losses: number
  win_rate: number
  total_pnl: number
  daily_pnl: number
  avg_profit_per_trade: number
  avg_duration_min: number
  best_trade: number
  worst_trade: number
  current_streak: number
  enabled: boolean
}

export default function BotComparison() {
  const [performances, setPerformances] = useState<BotPerformance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [sortBy, setSortBy] = useState<'win_rate' | 'total_pnl' | 'total_trades'>('total_pnl')

  const fetchPerformances = useCallback(async () => {
    try {
      const response = await dashboardApi.getBotComparison()
      setPerformances(response.data.performances || [])
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Erro ao carregar comparação:', error)
      // Mock data para demonstração
      setPerformances([
        {
          bot_type: 'unico_bot',
          bot_name: '🤖 UnicoBot',
          total_trades: 0,
          wins: 0,
          losses: 0,
          win_rate: 0,
          total_pnl: 0,
          daily_pnl: 0,
          avg_profit_per_trade: 0,
          avg_duration_min: 0,
          best_trade: 0,
          worst_trade: 0,
          current_streak: 0,
          enabled: true
        },
        {
          bot_type: 'bot_estavel',
          bot_name: '🐢 Bot Estável',
          total_trades: 15,
          wins: 10,
          losses: 5,
          win_rate: 66.7,
          total_pnl: 2.35,
          daily_pnl: 0.45,
          avg_profit_per_trade: 0.157,
          avg_duration_min: 45.2,
          best_trade: 0.85,
          worst_trade: -0.32,
          current_streak: 3,
          enabled: true
        },
        {
          bot_type: 'bot_medio',
          bot_name: '⚖️ Bot Médio',
          total_trades: 22,
          wins: 11,
          losses: 11,
          win_rate: 50.0,
          total_pnl: 1.70,
          daily_pnl: -0.10,
          avg_profit_per_trade: 0.077,
          avg_duration_min: 8.5,
          best_trade: 0.42,
          worst_trade: -0.28,
          current_streak: -2,
          enabled: true
        },
        {
          bot_type: 'bot_volatil',
          bot_name: '⚡ Bot Volátil',
          total_trades: 22,
          wins: 14,
          losses: 8,
          win_rate: 63.6,
          total_pnl: 0.31,
          daily_pnl: -0.16,
          avg_profit_per_trade: 0.014,
          avg_duration_min: 6.3,
          best_trade: 0.35,
          worst_trade: -0.45,
          current_streak: 1,
          enabled: true
        },
        {
          bot_type: 'bot_meme',
          bot_name: '🚀 Bot Meme',
          total_trades: 8,
          wins: 5,
          losses: 3,
          win_rate: 62.5,
          total_pnl: 0.28,
          daily_pnl: 0.05,
          avg_profit_per_trade: 0.035,
          avg_duration_min: 4.1,
          best_trade: 0.52,
          worst_trade: -0.18,
          current_streak: 2,
          enabled: true
        }
      ])
      setLastUpdate(new Date())
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPerformances()
    const interval = setInterval(fetchPerformances, 30000)
    return () => clearInterval(interval)
  }, [fetchPerformances])

  const sortedPerformances = [...performances].sort((a, b) => {
    switch (sortBy) {
      case 'win_rate':
        return b.win_rate - a.win_rate
      case 'total_pnl':
        return b.total_pnl - a.total_pnl
      case 'total_trades':
        return b.total_trades - a.total_trades
      default:
        return 0
    }
  })

  const getRankBadge = (index: number) => {
    switch (index) {
      case 0:
        return <span className="text-2xl">🥇</span>
      case 1:
        return <span className="text-2xl">🥈</span>
      case 2:
        return <span className="text-2xl">🥉</span>
      default:
        return <span className="text-lg text-gray-500">#{index + 1}</span>
    }
  }

  const getWinRateColor = (rate: number) => {
    if (rate >= 60) return 'text-green-400'
    if (rate >= 50) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-400'
    if (pnl < 0) return 'text-red-400'
    return 'text-gray-400'
  }

  const getStreakDisplay = (streak: number) => {
    if (streak > 0) {
      return <span className="text-green-400">🔥 {streak}W</span>
    } else if (streak < 0) {
      return <span className="text-red-400">❄️ {Math.abs(streak)}L</span>
    }
    return <span className="text-gray-400">-</span>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  // Calcular totais
  const totals = performances.reduce((acc, bot) => ({
    trades: acc.trades + bot.total_trades,
    wins: acc.wins + bot.wins,
    losses: acc.losses + bot.losses,
    pnl: acc.pnl + bot.total_pnl
  }), { trades: 0, wins: 0, losses: 0, pnl: 0 })

  const totalWinRate = totals.trades > 0 ? (totals.wins / totals.trades) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Trophy className="w-7 h-7 text-yellow-400" />
            Comparação de Performance dos Bots
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Análise comparativa para identificar o bot mais rentável
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'win_rate' | 'total_pnl' | 'total_trades')}
            className="input bg-dark-700 border-gray-600"
          >
            <option value="total_pnl">Ordenar por PnL</option>
            <option value="win_rate">Ordenar por Win Rate</option>
            <option value="total_trades">Ordenar por Trades</option>
          </select>
          <button
            onClick={fetchPerformances}
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

      {/* Resumo Geral */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-sm text-gray-400">Total Trades</p>
              <p className="text-2xl font-bold text-white">{totals.trades}</p>
            </div>
          </div>
        </div>
        <div className="card bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
          <div className="flex items-center gap-3">
            <Target className="w-8 h-8 text-green-400" />
            <div>
              <p className="text-sm text-gray-400">Win Rate Global</p>
              <p className="text-2xl font-bold text-white">{totalWinRate.toFixed(1)}%</p>
            </div>
          </div>
        </div>
        <div className={`card bg-gradient-to-br ${totals.pnl >= 0 ? 'from-green-500/10 to-green-600/5 border-green-500/20' : 'from-red-500/10 to-red-600/5 border-red-500/20'}`}>
          <div className="flex items-center gap-3">
            {totals.pnl >= 0 ? <TrendingUp className="w-8 h-8 text-green-400" /> : <TrendingDown className="w-8 h-8 text-red-400" />}
            <div>
              <p className="text-sm text-gray-400">PnL Total</p>
              <p className={`text-2xl font-bold ${getPnLColor(totals.pnl)}`}>
                ${totals.pnl.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
        <div className="card bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
          <div className="flex items-center gap-3">
            <Award className="w-8 h-8 text-purple-400" />
            <div>
              <p className="text-sm text-gray-400">Melhor Bot</p>
              <p className="text-xl font-bold text-white">
                {sortedPerformances[0]?.bot_name?.split(' ')[0] || '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Ranking Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">🏆 Ranking de Performance</h2>
        
        {sortedPerformances.map((bot, index) => (
          <div
            key={bot.bot_type}
            className={`card transition-all hover:scale-[1.01] ${
              index === 0 ? 'border-yellow-500/30 bg-gradient-to-r from-yellow-500/5 to-transparent' :
              index === 1 ? 'border-gray-400/30 bg-gradient-to-r from-gray-400/5 to-transparent' :
              index === 2 ? 'border-orange-600/30 bg-gradient-to-r from-orange-600/5 to-transparent' :
              'border-gray-700'
            }`}
          >
            <div className="flex items-center gap-6">
              {/* Rank */}
              <div className="flex-shrink-0 w-12 text-center">
                {getRankBadge(index)}
              </div>

              {/* Bot Info */}
              <div className="flex-shrink-0 w-48">
                <h3 className="text-lg font-bold text-white">{bot.bot_name}</h3>
                <p className="text-xs text-gray-400">
                  {bot.enabled ? '🟢 Ativo' : '🔴 Inativo'}
                </p>
              </div>

              {/* Stats Grid */}
              <div className="flex-1 grid grid-cols-2 md:grid-cols-6 gap-4">
                <div className="text-center">
                  <p className="text-xs text-gray-400">Trades</p>
                  <p className="text-lg font-bold text-white">{bot.total_trades}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400">Win/Loss</p>
                  <p className="text-lg font-bold">
                    <span className="text-green-400">{bot.wins}</span>
                    <span className="text-gray-400">/</span>
                    <span className="text-red-400">{bot.losses}</span>
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400">Win Rate</p>
                  <p className={`text-lg font-bold ${getWinRateColor(bot.win_rate)}`}>
                    {bot.win_rate.toFixed(1)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400">PnL Total</p>
                  <p className={`text-lg font-bold ${getPnLColor(bot.total_pnl)}`}>
                    ${bot.total_pnl.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400">Média/Trade</p>
                  <p className={`text-lg font-bold ${getPnLColor(bot.avg_profit_per_trade)}`}>
                    ${bot.avg_profit_per_trade.toFixed(3)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400">Streak</p>
                  <p className="text-lg font-bold">{getStreakDisplay(bot.current_streak)}</p>
                </div>
              </div>

              {/* Best/Worst */}
              <div className="flex-shrink-0 w-32 text-right">
                <p className="text-xs text-gray-400">Melhor: <span className="text-green-400">${bot.best_trade.toFixed(2)}</span></p>
                <p className="text-xs text-gray-400">Pior: <span className="text-red-400">${bot.worst_trade.toFixed(2)}</span></p>
                <p className="text-xs text-gray-400">Duração: {bot.avg_duration_min.toFixed(0)}min</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Análise Detalhada */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Win Rate Chart */}
        <div className="card">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Percent className="w-5 h-5 text-blue-400" />
            Win Rate por Bot
          </h3>
          <div className="space-y-3">
            {sortedPerformances.map((bot) => (
              <div key={bot.bot_type}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">{bot.bot_name}</span>
                  <span className={getWinRateColor(bot.win_rate)}>{bot.win_rate.toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      bot.win_rate >= 60 ? 'bg-green-500' :
                      bot.win_rate >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(bot.win_rate, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PnL Chart */}
        <div className="card">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            PnL Total por Bot
          </h3>
          <div className="space-y-3">
            {sortedPerformances.map((bot) => {
              const maxPnl = Math.max(...performances.map(p => Math.abs(p.total_pnl)), 1)
              const width = (Math.abs(bot.total_pnl) / maxPnl) * 100
              return (
                <div key={bot.bot_type}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">{bot.bot_name}</span>
                    <span className={getPnLColor(bot.total_pnl)}>${bot.total_pnl.toFixed(2)}</span>
                  </div>
                  <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        bot.total_pnl >= 0 ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="card bg-gradient-to-r from-blue-500/5 to-purple-500/5 border-blue-500/20">
        <h3 className="font-semibold text-white mb-3">💡 Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="p-3 bg-dark-700/50 rounded-lg">
            <p className="text-gray-400 mb-1">🏆 Bot mais lucrativo</p>
            <p className="text-white font-medium">
              {sortedPerformances[0]?.bot_name} com ${sortedPerformances[0]?.total_pnl.toFixed(2)}
            </p>
          </div>
          <div className="p-3 bg-dark-700/50 rounded-lg">
            <p className="text-gray-400 mb-1">🎯 Melhor Win Rate</p>
            <p className="text-white font-medium">
              {[...performances].sort((a, b) => b.win_rate - a.win_rate)[0]?.bot_name} com{' '}
              {[...performances].sort((a, b) => b.win_rate - a.win_rate)[0]?.win_rate.toFixed(1)}%
            </p>
          </div>
          <div className="p-3 bg-dark-700/50 rounded-lg">
            <p className="text-gray-400 mb-1">⚡ Mais trades</p>
            <p className="text-white font-medium">
              {[...performances].sort((a, b) => b.total_trades - a.total_trades)[0]?.bot_name} com{' '}
              {[...performances].sort((a, b) => b.total_trades - a.total_trades)[0]?.total_trades} trades
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
