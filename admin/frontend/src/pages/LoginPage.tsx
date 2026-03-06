import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

type LoginPageProps = {
  onLogin: (username: string, password: string) => Promise<void>
}

function LoginPage({ onLogin }: LoginPageProps) {
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setErrorMessage(null)

    const trimmedUsername = username.trim()
    if (!trimmedUsername || !password.trim()) {
      setErrorMessage('아이디와 비밀번호를 입력해주세요.')
      return
    }

    setLoading(true)
    try {
      await onLogin(trimmedUsername, password)
      navigate('/dashboard', { replace: true })
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '로그인에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page login-page">
      <div className="card auth-card">
        <h1>Admin Login</h1>
        <p className="muted">관리자 대시보드에 접속합니다.</p>

        <form onSubmit={handleSubmit} className="form-stack">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="admin"
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="password"
          />

          {errorMessage && <p className="error">{errorMessage}</p>}

          <button type="submit" disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <p className="muted switch-link">
          계정이 없나요? <Link to="/register">회원가입</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
