import { useEffect, useState } from 'react'
import { dashboardApi } from '../services/api'
import { TrendingUp, TrendingDown, Calendar, Search } from 'lucide-react'

interface Trade {
  id: number
  bot_name: string
  symbol: string
  side: string
  entry_price: number
  exit_price: number
  quantity: number
  pnl: number
  pnl_percent: number
  opened_at: string
  closed_at: string
  duration_minutes: number
}

export default function Trades() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filter, setFilter] = useState('')

  const fetchTrades = async () => {
    setIsLoading(true)
    try {
      const response = await dashboardApi.getTrades(page, 20)
      setTrades(response.data.items || [])
      setTotalPages(response.data.pages || 1)
    } catch (error) {
      console.error('Erro ao carregar trades:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTrades()
  }, [page])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('pt-BR')
  }

  const filteredTrades = trades.filter(trade =>
    trade.symbol.toLowerCase().includes(filter.toLowerCase()) ||
    trade.bot_name.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Histórico de Trades</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Buscar..."
            className="input pl-10 w-64"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                  <th className="pb-4 font-medium">Data</th>
                  <th className="pb-4 font-medium">Par</th>
                  <th className="pb-4 font-medium">Bot</th>
                  <th className="pb-4 font-medium">Lado</th>
                  <th className="pb-4 font-medium">Entrada</th>
                  <th className="pb-4 font-medium">Saída</th>
                  <th className="pb-4 font-medium text-right">PnL</th>
                  <th className="pb-4 font-medium text-right">%</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-dark-200/50">
                    <td className="py-4">
                      <div className="flex items-center gap-2 text-gray-300">
                        <Calendar className="w-4 h-4 text-gray-500" />
                        {formatDate(trade.closed_at)}
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="font-medium text-white">{trade.symbol}</span>
                    </td>
                    <td className="py-4">
                      <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                        {trade.bot_name}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 text-gray-300">{formatCurrency(trade.entry_price)}</td>
                    <td className="py-4 text-gray-300">{formatCurrency(trade.exit_price)}</td>
                    <td className="py-4 text-right">
                      <span className={`flex items-center justify-end gap-1 font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.pnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {formatCurrency(trade.pnl)}
                      </span>
                    </td>
                    <td className={`py-4 text-right font-medium ${trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary"
              >
                Anterior
              </button>
              <span className="text-gray-400">
                Página {page} de {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary"
              >
                Próxima
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
