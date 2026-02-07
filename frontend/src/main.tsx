import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'
import App from './App'
import './index.css'

const apiUrl = (import.meta.env.VITE_API_URL || '').trim()
const isDev = import.meta.env.DEV
const isLocalhostUrl = (url: string) => /^https?:\/\/localhost(:\d+)?(\/|$)/i.test(url)
let baseUrl = apiUrl
try {
  if (typeof window !== 'undefined' && window.location?.hostname?.includes?.('vercel.app')) {
    // Vercel이어도 VITE_API_URL이 localhost면 그대로 사용 → 로컬 백엔드만 쓸 때 BACKEND_URL 없이 동작
    baseUrl = apiUrl && isLocalhostUrl(apiUrl) ? apiUrl : '/api/proxy'
  } else if (isDev) {
    baseUrl = ''
  }
} catch (_) {
  baseUrl = apiUrl
}
axios.defaults.baseURL = baseUrl
if (!isDev) {
  axios.defaults.headers.common['Cache-Control'] = 'no-cache'
  axios.defaults.headers.common['Pragma'] = 'no-cache'
}
console.log('[Config] API base:', baseUrl || '(vite proxy)')

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null }
  static getDerivedStateFromError(error: Error) {
    return { error }
  }
  render() {
    if (this.state.error) {
      const err = this.state.error
      return (
        <div style={{ padding: 24, fontFamily: 'sans-serif', maxWidth: 600 }}>
          <h2 style={{ color: '#b91c1c' }}>앱 로드 중 오류</h2>
          <pre style={{ background: '#fef2f2', padding: 16, overflow: 'auto', fontSize: 12 }}>
            {err.name}: {err.message}
            {'\n\n'}
            {err.stack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}

function mount() {
  const el = document.getElementById('root')
  if (!el) {
    document.body.innerHTML = '<div style="padding:24px;font-family:sans-serif"><h2>root 요소 없음</h2></div>'
    return
  }
  try {
    const root = ReactDOM.createRoot(el)
    root.render(
      <React.StrictMode>
        <ErrorBoundary>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ErrorBoundary>
      </React.StrictMode>,
    )
  } catch (e) {
    el.innerHTML = `<div style="padding:24px;font-family:sans-serif;color:#b91c1c"><h2>초기화 오류</h2><pre>${String(e)}</pre></div>`
  }
}

mount()
