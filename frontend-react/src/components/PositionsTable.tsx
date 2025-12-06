import { Clock, TrendingUp, TrendingDown } from 'lucide-react'

interface Position {
  id: number
  bot_name: string
  symbol: string
  side: string
  entry_price: number
  current_price: number
  quantity: number
  pnl: number
  pnl_percent: number
  opened_at: string
}

interface PositionsTableProps {
  positions: Position[]
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  if (positions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p>Nenhuma posição aberta no momento</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
            <th className="pb-3 font-medium">Par</th>
            <th className="pb-3 font-medium">Bot</th>
            <th className="pb-3 font-medium">Lado</th>
            <th className="pb-3 font-medium">Entrada</th>
            <th className="pb-3 font-medium">Atual</th>
            <th className="pb-3 font-medium">Tempo</th>
            <th className="pb-3 font-medium text-right">PnL</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700/50">
          {positions.map((position) => (
            <tr key={position.id} className="hover:bg-dark-200/30">
              <td className="py-3">
                <span className="font-medium text-white">{position.symbol}</span>
              </td>
              <td className="py-3">
                <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300 capitalize">
                  {position.bot_name}
                </span>
              </td>
              <td className="py-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  position.side === 'buy' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {position.side.toUpperCase()}
                </span>
              </td>
              <td className="py-3 text-gray-300">{formatCurrency(position.entry_price)}</td>
              <td className="py-3 text-gray-300">{formatCurrency(position.current_price)}</td>
              <td className="py-3">
                <span className="flex items-center gap-1 text-gray-400 text-sm">
                  <Clock className="w-3 h-3" />
                  {formatTime(position.opened_at)}
                </span>
              </td>
              <td className="py-3 text-right">
                <div className={`flex items-center justify-end gap-1 font-medium ${
                  position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {position.pnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {formatCurrency(position.pnl)}
                  <span className="text-xs opacity-75">
                    ({position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%)
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
