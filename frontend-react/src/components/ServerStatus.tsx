import React, { useState, useEffect } from 'react';
import { Server, CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface HealthData {
  status: string;
  version: string;
  timestamp: string;
  uptime_seconds: number;
  uptime_human: string;
  environment: {
    debug: boolean;
    host: string;
    port: number;
  };
  data: {
    data_dir_exists: boolean;
    config_exists: boolean;
  };
  system: {
    disk_usage_percent: number;
    python_version: string;
  };
}

export const ServerStatus: React.FC<{ apiUrl: string }> = ({ apiUrl }) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${apiUrl}/health`, {
          method: 'GET',
          timeout: 5000,
        });
        if (response.ok) {
          const data = await response.json();
          setHealth(data);
          setIsOnline(true);
        } else {
          setIsOnline(false);
        }
      } catch (error) {
        setIsOnline(false);
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // A cada 30s
    return () => clearInterval(interval);
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Server className="w-5 h-5 text-blue-400" />
            <div>
              <h3 className="text-white font-semibold">Servidor AWS</h3>
              <p className="text-gray-400 text-sm">Verificando...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 border border-red-700 bg-red-900/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <h3 className="text-white font-semibold">Servidor AWS</h3>
              <p className="text-red-300 text-sm">❌ Offline</p>
            </div>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-green-700 bg-green-900/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-400" />
          <div>
            <h3 className="text-white font-semibold">Servidor AWS</h3>
            <p className="text-green-300 text-sm">✅ Online · v{health?.version}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {/* Uptime */}
        <div className="bg-gray-700/50 rounded p-2">
          <div className="flex items-center gap-2 text-gray-300">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>Uptime</span>
          </div>
          <p className="text-white font-semibold mt-1">{health?.uptime_human || 'N/A'}</p>
        </div>

        {/* Disco */}
        <div className="bg-gray-700/50 rounded p-2">
          <div className="text-gray-300">Disco Usado</div>
          <p className="text-white font-semibold mt-1">{health?.system.disk_usage_percent || 0}%</p>
          <div className="w-full bg-gray-600 rounded-full h-1.5 mt-1">
            <div
              className={`h-1.5 rounded-full ${
                (health?.system.disk_usage_percent || 0) > 80 ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ width: `${health?.system.disk_usage_percent || 0}%` }}
            ></div>
          </div>
        </div>

        {/* Configuração */}
        <div className="bg-gray-700/50 rounded p-2">
          <div className="text-gray-300">Status Config</div>
          <p className={`font-semibold mt-1 ${health?.data.config_exists ? 'text-green-400' : 'text-red-400'}`}>
            {health?.data.config_exists ? '✅ OK' : '❌ Faltando'}
          </p>
        </div>

        {/* Dados */}
        <div className="bg-gray-700/50 rounded p-2">
          <div className="text-gray-300">Diretório Data</div>
          <p className={`font-semibold mt-1 ${health?.data.data_dir_exists ? 'text-green-400' : 'text-red-400'}`}>
            {health?.data.data_dir_exists ? '✅ Existe' : '❌ Criar'}
          </p>
        </div>
      </div>

      <div className="mt-3 text-xs text-gray-400 border-t border-gray-700 pt-2">
        <p>Host: {health?.environment.host}:{health?.environment.port}</p>
        <p>Última verificação: {new Date(health?.timestamp || '').toLocaleTimeString('pt-BR')}</p>
      </div>
    </div>
  );
};
