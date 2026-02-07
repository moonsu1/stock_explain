import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'
import App from './App'
import { getApiBaseUrl } from './utils/apiBase'
import './index.css'

// API base: Vercel이면 같은 오리진 프록시(/api/proxy) 사용 → 카톡 인앱 브라우저 대응
axios.defaults.baseURL = getApiBaseUrl() || import.meta.env.VITE_API_URL || ''
console.log('[Config] API base:', axios.defaults.baseURL || '(local)')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
