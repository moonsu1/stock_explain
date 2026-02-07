import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'
import App from './App'
import './index.css'

const apiUrl = import.meta.env.VITE_API_URL || ''
let baseUrl = apiUrl
try {
  if (typeof window !== 'undefined' && window.location?.hostname?.includes?.('vercel.app')) {
    baseUrl = '/api/proxy'
  }
} catch (_) {
  baseUrl = apiUrl
}
axios.defaults.baseURL = baseUrl
console.log('[Config] API base:', baseUrl || '(local)')

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
