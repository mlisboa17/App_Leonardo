import { useEffect } from 'react'
import { useDashboardStore } from '../stores/dashboardStore'
import { 
  TrendingUp, TrendingDown, DollarSign, Activity, 
  Target, Percent, Bot, AlertTriangle 
} from 'lucide-react'
import PnlChart from '../components/PnlChart'
import BotCard from '../components/BotCard'
import PositionsTable from '../components/PositionsTable'

export default function Dashboard() {
  const { summary, bots, positions, fetchSummary, fetchBots, fetchPositions, isLoading } = useDashboardStore()

  useEffect(() => {
    fetchSummary()
    fetchBots()
    fetchPositions()

    // Atualizar a cada 30 segundos
    const interval = setInterval(() => {
      fetchSummary()
      fetchBots()
      fetchPositions()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchSummary, fetchBots, fetchPositions])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  if (isLoading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Saldo Total"
          value={formatCurrency(summary?.total_balance || 0)}
          icon={<DollarSign className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="PnL Hoje"
          value={formatCurrency(summary?.pnl_today || 0)}
          subtitle={formatPercent(summary?.pnl_today || 0)}
          icon={summary?.pnl_today && summary.pnl_today >= 0 ? <TrendingUp className="w-6 h-6" /> : <TrendingDown className="w-6 h-6" />}
          color={summary?.pnl_today && summary.pnl_today >= 0 ? 'green' : 'red'}
        />
        <StatCard
          title="Win Rate"
          value={`${(summary?.win_rate || 0).toFixed(1)}%`}
          icon={<Target className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Posições Abertas"
          value={String(summary?.open_positions || 0)}
          subtitle={`${formatCurrency(summary?.in_positions || 0)} alocado`}
          icon={<Activity className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* PnL Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Evolução do PnL</h2>
        <PnlChart />
      </div>

      {/* Bots Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Status dos Bots</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {bots.map((bot) => (
            <BotCard key={bot.name} bot={bot} />
          ))}
          {bots.length === 0 && (
            <div className="col-span-full card text-center py-8 text-gray-400">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Nenhum bot configurado</p>
            </div>
          )}
        </div>
      </div>

      {/* Positions Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Posições Abertas</h2>
          {positions.length > 0 && (
            <span className="text-sm text-gray-400">{positions.length} posições</span>
          )}
        </div>
        <PositionsTable positions={positions} />
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string
  subtitle?: string
  icon: React.ReactNode
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange'
}

function StatCard({ title, value, subtitle, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-green-500/10 text-green-400',
    red: 'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
    orange: 'bg-orange-500/10 text-orange-400',
  }

  return (
    <div className="card card-hover">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className={`text-sm mt-1 ${color === 'green' ? 'text-green-400' : color === 'red' ? 'text-red-400' : 'text-gray-400'}`}>{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
