# R7 Trading Bot - Frontend React

Dashboard moderno em React para controle do bot de trading.

## 🚀 Tecnologias

- **React 18** com TypeScript
- **Vite** para build rápido
- **TailwindCSS** para estilização
- **Zustand** para gerenciamento de estado
- **React Router** para navegação
- **Recharts** para gráficos
- **Axios** para requisições HTTP
- **Lucide React** para ícones

## 📁 Estrutura

```
frontend-react/
├── src/
│   ├── components/      # Componentes reutilizáveis
│   │   ├── Layout.tsx       # Layout principal com sidebar
│   │   ├── BotCard.tsx      # Card de status do bot
│   │   ├── PnlChart.tsx     # Gráfico de PnL
│   │   └── PositionsTable.tsx
│   ├── pages/           # Páginas da aplicação
│   │   ├── Login.tsx        # Tela de login
│   │   ├── Dashboard.tsx    # Dashboard principal
│   │   ├── Positions.tsx    # Posições abertas
│   │   ├── Trades.tsx       # Histórico de trades
│   │   └── Config.tsx       # Configurações
│   ├── services/        # Serviços e APIs
│   │   └── api.ts           # Cliente HTTP
│   ├── stores/          # Estado global (Zustand)
│   │   ├── authStore.ts     # Autenticação
│   │   └── dashboardStore.ts
│   ├── App.tsx          # Rotas
│   ├── main.tsx         # Entrada
│   └── index.css        # Estilos globais
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🛠️ Instalação

### Pré-requisitos
- Node.js 18+ 
- npm ou yarn

### Instalar dependências
```bash
cd frontend-react
npm install
```

### Rodar em desenvolvimento
```bash
npm run dev
```

Acesse: http://localhost:3000

### Build para produção
```bash
npm run build
```

## 🔐 Autenticação

O frontend usa autenticação JWT:
- Token armazenado no localStorage
- Auto-redirect para /login se não autenticado
- Refresh automático quando token expira

### Credenciais padrão
- **Usuário:** admin
- **Senha:** admin123

## 📊 Funcionalidades

### Dashboard
- Resumo de saldo e PnL
- Gráfico de evolução do PnL
- Status dos 4 bots
- Posições abertas em tempo real

### Posições
- Lista de todas as posições
- PnL em tempo real
- Botão para fechar posição manualmente

### Histórico
- Tabela paginada de trades
- Filtro por símbolo/bot
- Estatísticas detalhadas

### Configurações
- Ajustar parâmetros de cada bot
- Habilitar/desabilitar bots
- Configurações globais

### Emergência
- Botão de parada de emergência na sidebar
- Para todos os bots imediatamente

## 🎨 Temas

Tema dark por padrão com cores:
- Verde primário (#22c55e)
- Backgrounds escuros (#020617, #0f172a, #1e293b)
- Textos em tons de cinza

## 🔧 Variáveis de Ambiente

Crie um arquivo `.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

## 📝 Notas

- Atualização automática a cada 30 segundos
- Proxy configurado para /api em desenvolvimento
- Responsivo para desktop e tablet
