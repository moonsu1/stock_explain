import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Analysis from './pages/Analysis'
import AutoTrade from './pages/AutoTrade'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="auto-trade" element={<AutoTrade />} />
      </Route>
    </Routes>
  )
}

export default App
