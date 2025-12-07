import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Positions from './pages/Positions'
import Trades from './pages/Trades'
import Config from './pages/Config'
import BotControl from './pages/BotControl'
import Indicators from './pages/Indicators'
import BotComparison from './pages/BotComparison'
import Layout from './components/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="positions" element={<Positions />} />
        <Route path="trades" element={<Trades />} />
        <Route path="bots" element={<BotControl />} />
        <Route path="indicators" element={<Indicators />} />
        <Route path="comparison" element={<BotComparison />} />
        <Route path="config" element={<Config />} />
      </Route>
    </Routes>
  )
}

export default App
