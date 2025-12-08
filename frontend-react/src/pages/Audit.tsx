import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, Download, Filter } from 'lucide-react'

interface AuditEvent {
  timestamp: string
  event_type: string
  severity: 'info' | 'warning' | 'critical'
  source: string
  target: string
  action: string
  details: Record<string, unknown>
  user_id?: string
}

interface AuditSummary {
  by_type: Record<string, number>
  by_severity: Record<string, number>
  by_source: Record<string, number>
  total_events: number
}

export default function Audit() {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [summary, setSummary] = useState<AuditSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null)
  const [limit, setLimit] = useState(100)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const fetchEvents = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('limit', limit.toString())
      if (selectedType) params.append('event_type', selectedType)
      if (selectedSource) params.append('source', selectedSource)
      if (selectedSeverity) params.append('severity', selectedSeverity)

      const response = await fetch(`/api/audit/events?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })

      const data = await response.json()
      if (data.success) {
        setEvents(data.data.events)
      } else {
        setMessage({ type: 'error', text: data.error || 'Erro ao buscar eventos' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Erro: ${error instanceof Error ? error.message : 'Erro desconhecido'}` })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/audit/events/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })

      const data = await response.json()
      if (data.success) {
        setSummary(data.data)
      }
    } catch (error) {
      console.error('Erro ao buscar sumário:', error)
    }
  }

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedType) params.append('event_type', selectedType)

      const response = await fetch(`/api/audit/export?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })

      const data = await response.json()
      if (data.success) {
        setMessage({ type: 'success', text: `${data.data.message}` })
      } else {
        setMessage({ type: 'error', text: data.error || 'Erro ao exportar' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Erro: ${error instanceof Error ? error.message : 'Erro desconhecido'}` })
    }
  }

  useEffect(() => {
    fetchEvents()
    fetchSummary()
  }, [selectedType, selectedSource, selectedSeverity, limit])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-700 bg-red-50'
      case 'warning':
        return 'text-yellow-700 bg-yellow-50'
      default:
        return 'text-blue-700 bg-blue-50'
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <span className="px-2 py-1 bg-red-200 text-red-800 rounded text-xs font-semibold">CRÍTICO</span>
      case 'warning':
        return <span className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded text-xs font-semibold">AVISO</span>
      default:
        return <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-xs font-semibold">INFO</span>
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-2">📋 Auditoria</h1>
        <p className="text-gray-600">Registro detalhado de todas as ações do sistema</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {message.text}
        </div>
      )}

      {/* Sumário */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-3xl font-bold text-blue-600">{summary.total_events}</div>
            <div className="text-gray-600 text-sm mt-1">Total de Eventos</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-lg font-semibold text-gray-700">Por Tipo</div>
            <div className="mt-2 space-y-1 text-sm">
              {Object.entries(summary.by_type).slice(0, 3).map(([type, count]) => (
                <div key={type} className="flex justify-between">
                  <span>{type}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-lg font-semibold text-gray-700">Por Severidade</div>
            <div className="mt-2 space-y-1 text-sm">
              {Object.entries(summary.by_severity).map(([severity, count]) => (
                <div key={severity} className="flex justify-between">
                  <span className="capitalize">{severity}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-lg font-semibold text-gray-700">Por Origem</div>
            <div className="mt-2 space-y-1 text-sm">
              {Object.entries(summary.by_source).slice(0, 3).map(([source, count]) => (
                <div key={source} className="flex justify-between">
                  <span className="capitalize">{source}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter size={18} />
          <h2 className="text-lg font-semibold">Filtros</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Evento</label>
            <select
              value={selectedType || ''}
              onChange={(e) => setSelectedType(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="restart">Restart</option>
              <option value="stop">Stop</option>
              <option value="config_change">Config Change</option>
              <option value="trade">Trade</option>
              <option value="error">Error</option>
              <option value="position_change">Position Change</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Origem</label>
            <select
              value={selectedSource || ''}
              onChange={(e) => setSelectedSource(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas</option>
              <option value="api">API</option>
              <option value="watcher">Watcher</option>
              <option value="bot">Bot</option>
              <option value="coordinator">Coordinator</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severidade</label>
            <select
              value={selectedSeverity || ''}
              onChange={(e) => setSelectedSeverity(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Limite</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={500}>500</option>
              <option value={1000}>1000</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={fetchEvents}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
              Atualizar
            </button>
            <button
              onClick={handleExport}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
            >
              <Download size={16} />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Lista de eventos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Eventos ({events.length})</h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-600">
            <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
            Carregando eventos...
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            Nenhum evento encontrado
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Timestamp</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Tipo</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Severidade</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Origem</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Alvo</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Ação</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event, idx) => (
                  <tr key={idx} className={`border-b border-gray-200 hover:bg-gray-50 ${getSeverityColor(event.severity)}`}>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="font-medium">{event.event_type}</span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {getSeverityBadge(event.severity)}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-xs">
                        {event.source}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">{event.target}</td>
                    <td className="px-6 py-4 text-sm">{event.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
