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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
