import { Navigate, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { DashboardPageNew } from './pages/DashboardPageNew'
import { fetchMe, login, register } from './services/api'

const TOKEN_KEY = 'admin_access_token'

function App() {
  const [username, setUsername] = useState<string | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    const run = async () => {
      const savedToken = localStorage.getItem(TOKEN_KEY)
      if (!savedToken) {
        setCheckingSession(false)
        return
      }

      try {
        const me = await fetchMe(savedToken)
        setToken(savedToken)
        setUsername(me.username)
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUsername(null)
      } finally {
        setCheckingSession(false)
      }
    }

    void run()
  }, [])

  const handleLogin = async (nextUsername: string, password: string) => {
    const result = await login(nextUsername, password)
    localStorage.setItem(TOKEN_KEY, result.access_token)
    setToken(result.access_token)
    setUsername(nextUsername)
  }

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUsername(null)
  }

  const handleRegister = async (nextUsername: string, email: string, password: string) => {
    await register({ username: nextUsername, email, password })
  }

  if (checkingSession) {
    return <div className="page">세션 확인 중...</div>
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage onLogin={handleLogin} />}
      />

      <Route
        path="/register"
        element={<RegisterPage onRegister={handleRegister} />}
      />

      <Route
        path="/dashboard"
        element={
          username && token ? (
            <DashboardPageNew username={username} token={token} onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="*"
        element={<Navigate to={username ? '/dashboard' : '/login'} replace />}
      />
    </Routes>
  )
}

export default App
