import { Play, Pause, TrendingUp, TrendingDown } from 'lucide-react'
import { useDashboardStore } from '../stores/dashboardStore'

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

interface BotCardProps {
  bot: BotStatus
}

export default function BotCard({ bot }: BotCardProps) {
  const { startBot, stopBot } = useDashboardStore()

  const isRunning = bot.status === 'running'
  const pnlColor = bot.pnl_today >= 0 ? 'text-green-400' : 'text-red-400'

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const handleToggle = async () => {
    if (isRunning) {
      await stopBot(bot.name)
    } else {
      await startBot(bot.name)
    }
  }

  const botColors: Record<string, string> = {
    estavel: 'from-blue-500/20 to-blue-600/5 border-blue-500/30',
    medio: 'from-purple-500/20 to-purple-600/5 border-purple-500/30',
    volatil: 'from-orange-500/20 to-orange-600/5 border-orange-500/30',
    meme: 'from-pink-500/20 to-pink-600/5 border-pink-500/30',
  }

  const botIcons: Record<string, string> = {
    estavel: '🛡️',
    medio: '⚖️',
    volatil: '⚡',
    meme: '🚀',
  }

  return (
    <div className={`card card-hover bg-gradient-to-br ${botColors[bot.name] || 'from-gray-500/20 to-gray-600/5 border-gray-500/30'}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{botIcons[bot.name] || '🤖'}</span>
          <div>
            <h3 className="font-semibold text-white capitalize">{bot.name}</h3>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
              <span className="text-xs text-gray-400">{isRunning ? 'Ativo' : 'Parado'}</span>
            </div>
          </div>
        </div>
        <button
          onClick={handleToggle}
          className={`p-2 rounded-lg transition-colors ${
            isRunning 
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
          }`}
        >
          {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm">PnL Hoje</span>
          <span className={`font-medium flex items-center gap-1 ${pnlColor}`}>
            {bot.pnl_today >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            {formatCurrency(bot.pnl_today)}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm">Trades</span>
          <span className="text-white">{bot.trades_today}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm">Win Rate</span>
          <span className="text-white">{bot.win_rate.toFixed(1)}%</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm">Posições</span>
          <span className="text-white">{bot.open_positions}</span>
        </div>
      </div>

      {/* Progress bar for capital */}
      <div className="mt-4 pt-4 border-t border-gray-700/50">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
          <span>Capital Alocado</span>
          <span>{formatCurrency(bot.capital_allocated)}</span>
        </div>
        <div className="h-1.5 bg-dark-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-primary-500 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, (bot.capital_allocated / 500) * 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}
