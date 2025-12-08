import { Shield } from 'lucide-react'

export default function Security() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-yellow-500/10">
          <Shield className="w-5 h-5 text-yellow-400" />
        </div>
        <h2 className="text-lg font-semibold text-white">Segurança</h2>
      </div>
      <div className="card">
        <h3 className="font-medium text-yellow-400 mb-2">Recomendações de Segurança</h3>
        <ul className="list-disc pl-6 text-gray-300 text-sm space-y-1">
          <li>Use autenticação de dois fatores (2FA) na corretora e no dashboard.</li>
          <li>Troque suas senhas periodicamente.</li>
          <li>Nunca compartilhe sua chave de API ou senha.</li>
          <li>Monitore acessos suspeitos e ative alertas.</li>
          <li>Mantenha backups regulares das configurações.</li>
        </ul>
      </div>
    </div>
  )
}
