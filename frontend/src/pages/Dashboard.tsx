import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart2, X } from 'lucide-react'
import axios from 'axios'

interface IndexData {
  name: string
  value: number
  change: number
  changePercent: number
}

// TradingView 심볼 매핑 (무료 위젯용)
const chartSymbols: Record<string, string> = {
  '코스피': 'TVC:KOSPI',
  '코스닥': 'TVC:KOSDAQ', 
  '나스닥': 'NASDAQ:IXIC',
}

interface PortfolioSummary {
  totalValue: number
  totalProfit: number
  profitPercent: number
}

export default function Dashboard() {
  const [indices, setIndices] = useState<IndexData[]>([])
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [chartModal, setChartModal] = useState<{ show: boolean; name: string; symbol: string }>({
    show: false,
    name: '',
    symbol: ''
  })

  const openChart = (name: string) => {
    const symbol = chartSymbols[name] || 'KRX:KOSPI'
    setChartModal({ show: true, name, symbol })
  }

  const closeChart = () => {
    setChartModal({ show: false, name: '', symbol: '' })
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [indicesRes, portfolioRes] = await Promise.all([
          axios.get('/api/market/indices'),
          axios.get('/api/portfolio/summary'),
        ])
        setIndices(indicesRes.data)
        setPortfolio(portfolioRes.data)
      } catch (error) {
        console.error('데이터 로딩 실패:', error)
        // 더미 데이터 설정
        setIndices([
          { name: '코스피', value: 2650.28, change: 15.32, changePercent: 0.58 },
          { name: '코스닥', value: 862.45, change: -8.21, changePercent: -0.94 },
          { name: '나스닥', value: 15628.95, change: 128.52, changePercent: 0.83 },
        ])
        setPortfolio({
          totalValue: 15250000,
          totalProfit: 1250000,
          profitPercent: 8.93,
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-500 mt-1">실시간 시장 현황과 내 포트폴리오</p>
      </div>

      {/* 지수 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {indices.map((index) => (
          <div key={index.name} className="card">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-gray-500">{index.name}</p>
                <p className="text-2xl font-bold mt-1">{index.value.toLocaleString()}</p>
              </div>
              <div className={`p-2 rounded-lg ${index.change >= 0 ? 'bg-up' : 'bg-down'}`}>
                {index.change >= 0 ? (
                  <TrendingUp className="w-5 h-5 text-red-500" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-blue-500" />
                )}
              </div>
            </div>
            <div className="mt-4 flex justify-between items-center">
              <span className={index.change >= 0 ? 'text-up' : 'text-down'}>
                {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)} ({index.changePercent.toFixed(2)}%)
              </span>
              <button
                onClick={() => openChart(index.name)}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <BarChart2 className="w-4 h-4" />
                차트
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 포트폴리오 요약 */}
      {portfolio && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary-50 rounded-lg">
                <DollarSign className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">총 평가금액</p>
                <p className="text-2xl font-bold">{portfolio.totalValue.toLocaleString()}원</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${portfolio.totalProfit >= 0 ? 'bg-up' : 'bg-down'}`}>
                <Activity className={`w-6 h-6 ${portfolio.totalProfit >= 0 ? 'text-red-500' : 'text-blue-500'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">총 수익</p>
                <p className={`text-2xl font-bold ${portfolio.totalProfit >= 0 ? 'text-up' : 'text-down'}`}>
                  {portfolio.totalProfit >= 0 ? '+' : ''}{portfolio.totalProfit.toLocaleString()}원
                  <span className="text-base ml-2">({portfolio.profitPercent.toFixed(2)}%)</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 빠른 안내 */}
      <div className="card bg-gradient-to-r from-primary-50 to-blue-50">
        <h3 className="font-semibold text-gray-900">시작하기</h3>
        <p className="text-sm text-gray-600 mt-2">
          키움증권 Open API+에 로그인하면 실시간 데이터를 확인할 수 있어요.
          아직 연동되지 않았다면 포트폴리오 페이지에서 로그인해주세요.
        </p>
      </div>

      {/* 차트 모달 */}
      {chartModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold text-lg">{chartModal.name} 차트</h3>
              <button
                onClick={closeChart}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="h-[500px]">
              <iframe
                src={`https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=${chartModal.symbol}&interval=D&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Asia%2FSeoul&withdateranges=1&showpopupbutton=1&locale=kr`}
                style={{ width: '100%', height: '100%' }}
                frameBorder="0"
                allowTransparency={true}
                scrolling="no"
                allowFullScreen
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
