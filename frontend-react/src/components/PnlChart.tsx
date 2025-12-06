import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { dashboardApi } from '../services/api'

interface ChartData {
  labels: string[]
  pnl: number[]
  cumulative_pnl: number[]
  trades: number[]
}

export default function PnlChart() {
  const [data, setData] = useState<ChartData | null>(null)
  const [period, setPeriod] = useState('30d')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const response = await dashboardApi.getPnlChart(period)
        setData(response.data)
      } catch (error) {
        console.error('Erro ao carregar gráfico:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [period])

  if (isLoading || !data) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  const chartData = data.labels.map((label, index) => ({
    date: label,
    pnl: data.pnl[index],
    cumulative: data.cumulative_pnl[index],
    trades: data.trades[index],
  }))

  const periods = [
    { value: '7d', label: '7 dias' },
    { value: '30d', label: '30 dias' },
    { value: '90d', label: '90 dias' },
  ]

  return (
    <div>
      <div className="flex items-center justify-end gap-2 mb-4">
        {periods.map((p) => (
          <button
            key={p.value}
            onClick={() => setPeriod(p.value)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              period === p.value
                ? 'bg-primary-600 text-white'
                : 'bg-dark-200 text-gray-400 hover:text-white'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #374151',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#9ca3af' }}
              formatter={(value: number, name: string) => [
                `$${value.toFixed(2)}`,
                name === 'cumulative' ? 'PnL Acumulado' : 'PnL Diário'
              ]}
            />
            <Area
              type="monotone"
              dataKey="cumulative"
              stroke="#22c55e"
              fillOpacity={1}
              fill="url(#colorPnl)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
