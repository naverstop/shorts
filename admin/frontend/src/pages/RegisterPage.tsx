import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

type RegisterPageProps = {
  onRegister: (username: string, email: string, password: string) => Promise<void>
}

function RegisterPage({ onRegister }: RegisterPageProps) {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setErrorMessage(null)

    if (!username.trim() || !email.trim() || !password.trim()) {
      setErrorMessage('모든 항목을 입력해주세요.')
      return
    }

    setLoading(true)
    try {
      await onRegister(username.trim(), email.trim(), password)
      navigate('/login', { replace: true })
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page login-page">
      <div className="card auth-card">
        <h1>Admin Register</h1>
        <p className="muted">관리자 계정을 생성합니다.</p>

        <form onSubmit={handleSubmit} className="form-stack">
          <label htmlFor="register-username">Username</label>
          <input
            id="register-username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="admin"
          />

          <label htmlFor="register-email">Email</label>
          <input
            id="register-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="admin@example.com"
          />

          <label htmlFor="register-password">Password</label>
          <input
            id="register-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="8자 이상"
          />

          {errorMessage && <p className="error">{errorMessage}</p>}

          <button type="submit" disabled={loading}>
            {loading ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <p className="muted switch-link">
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
