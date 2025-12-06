import { useEffect, useState } from 'react'
import { dashboardApi, actionsApi } from '../services/api'
import { X, TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react'

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
  stop_loss?: number
  take_profit?: number
}

export default function Positions() {
  const [positions, setPositions] = useState<Position[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchPositions = async () => {
    try {
      const response = await dashboardApi.getPositions(1, 100)
      setPositions(response.data.items || [])
    } catch (error) {
      console.error('Erro ao carregar posições:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchPositions()
    const interval = setInterval(fetchPositions, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleClosePosition = async (id: number) => {
    if (!confirm('Tem certeza que deseja fechar esta posição?')) return
    
    try {
      await actionsApi.closePosition(id, 'Fechamento manual')
      fetchPositions()
    } catch (error) {
      console.error('Erro ao fechar posição:', error)
    }
  }

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
        <h1 className="text-2xl font-bold text-white">Posições Abertas</h1>
        <span className="text-gray-400">{positions.length} posições</span>
      </div>

      {positions.length === 0 ? (
        <div className="card text-center py-12">
          <DollarSign className="w-16 h-16 mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400 text-lg">Nenhuma posição aberta</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {positions.map((position) => (
            <div key={position.id} className="card card-hover">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${position.pnl >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    {position.pnl >= 0 ? (
                      <TrendingUp className="w-6 h-6 text-green-400" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-red-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-lg">{position.symbol}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${position.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {position.side.toUpperCase()}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                        {position.bot_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
                      <span>Entrada: {formatCurrency(position.entry_price)}</span>
                      <span>Atual: {formatCurrency(position.current_price)}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(position.opened_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className={`text-xl font-bold ${position.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatCurrency(position.pnl)}
                    </p>
                    <p className={`text-sm ${position.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%
                    </p>
                  </div>
                  <button
                    onClick={() => handleClosePosition(position.id)}
                    className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                    title="Fechar posição"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
