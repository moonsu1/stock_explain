import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'
import App from './App'
import './index.css'

// API 기본 URL 설정
const apiUrl = import.meta.env.VITE_API_URL || ''
axios.defaults.baseURL = apiUrl
console.log('[Config] API URL:', apiUrl || '(local)')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
