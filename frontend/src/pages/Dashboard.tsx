import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart2, X, CheckCircle } from 'lucide-react'
import axios from 'axios'
import { getSavedPortfolio } from '../utils/portfolioStorage'

interface IndexData {
  name: string
  value: number
  change: number
  changePercent: number
}

// 네이버 금융 차트 URL 매핑
const chartUrls: Record<string, string> = {
  '코스피': 'https://ssl.pstatic.net/imgfinance/chart/mobile/candle/day/KOSPI_end.png',
  '코스닥': 'https://ssl.pstatic.net/imgfinance/chart/mobile/candle/day/KOSDAQ_end.png', 
  '나스닥': 'https://ssl.pstatic.net/imgfinance/chart/world/candle/day/NAS@IXIC.png',
  '니케이225': 'https://ssl.pstatic.net/imgfinance/chart/world/candle/day/JPX@NI225.png',
  '금': 'https://ssl.pstatic.net/imgfinance/chart/marketindex/CMDT_GC.png',
  '은': 'https://ssl.pstatic.net/imgfinance/chart/marketindex/area/month/CMDT_SI.png',
  '구리': 'https://ssl.pstatic.net/imgfinance/chart/marketindex/CMDT_HG.png',
}

// 네이버 금융 상세 페이지 URL
const detailUrls: Record<string, string> = {
  '코스피': 'https://m.stock.naver.com/domestic/index/KOSPI/total',
  '코스닥': 'https://m.stock.naver.com/domestic/index/KOSDAQ/total',
  '나스닥': 'https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC',
  '니케이225': 'https://finance.naver.com/world/sise.naver?symbol=JPX@NI225',
  '금': 'https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_GC',
  '은': 'https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_SI',
  '구리': 'https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_HG',
}

interface PortfolioSummary {
  totalValue: number
  totalProfit: number
  profitPercent: number
}

const DUMMY_INDICES: IndexData[] = [
  { name: '코스피', value: 2650.28, change: 15.32, changePercent: 0.58 },
  { name: '코스닥', value: 862.45, change: -8.21, changePercent: -0.94 },
  { name: '나스닥', value: 15628.95, change: 128.52, changePercent: 0.83 },
]
const DUMMY_COMMODITIES: IndexData[] = [
  { name: '니케이225', value: 38500.00, change: 150.00, changePercent: 0.39 },
  { name: '금', value: 2850.50, change: 12.30, changePercent: 0.43 },
  { name: '은', value: 32.15, change: -0.25, changePercent: -0.77 },
  { name: '구리', value: 4.25, change: 0.05, changePercent: 1.19 },
]

function normalizePortfolio(raw: unknown): PortfolioSummary | null {
  if (raw == null || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  const totalValue = Number(o.totalValue ?? o.total_value) || 0
  const totalProfit = Number(o.totalProfit ?? o.total_profit) ?? 0
  const profitPercent = Number(o.profitPercent ?? o.profit_percent) ?? 0
  return { totalValue, totalProfit, profitPercent }
}

export default function Dashboard() {
  const [indices, setIndices] = useState<IndexData[]>([])
  const [commodities, setCommodities] = useState<IndexData[]>([])
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [chartModal, setChartModal] = useState<{ show: boolean; name: string; symbol: string }>({
    show: false,
    name: '',
    symbol: ''
  })
  const [chartError, setChartError] = useState(false)
  const [portfolioFromManual, setPortfolioFromManual] = useState(false)
  const [apiFailed, setApiFailed] = useState(false)

  const openChart = (name: string) => {
    setChartError(false)
    setChartModal({ show: true, name, symbol: '' })
  }

  const closeChart = () => {
    setChartModal({ show: false, name: '', symbol: '' })
    setChartError(false)
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [indicesRes, commoditiesRes, portfolioRes] = await Promise.all([
          axios.get('/api/market/indices'),
          axios.get('/api/market/commodities'),
          axios.get('/api/portfolio/summary'),
        ])
        setApiFailed(false)
        const indicesArr = Array.isArray(indicesRes.data) ? indicesRes.data : []
        const commoditiesArr = Array.isArray(commoditiesRes.data) ? commoditiesRes.data : []
        setIndices(indicesArr.length > 0 ? indicesArr : DUMMY_INDICES)
        setCommodities(commoditiesArr.length > 0 ? commoditiesArr : DUMMY_COMMODITIES)
        const saved = getSavedPortfolio()
        if (saved) {
          setPortfolio(normalizePortfolio(saved) ?? { totalValue: 0, totalProfit: 0, profitPercent: 0 })
          setPortfolioFromManual(true)
        } else {
          setPortfolio(normalizePortfolio(portfolioRes.data) ?? { totalValue: 0, totalProfit: 0, profitPercent: 0 })
        }
      } catch (error) {
        console.error('데이터 로딩 실패:', error)
        setApiFailed(true)
        setIndices(DUMMY_INDICES)
        setCommodities(DUMMY_COMMODITIES)
        const saved = getSavedPortfolio()
        if (saved) {
          setPortfolio(normalizePortfolio(saved) ?? { totalValue: 0, totalProfit: 0, profitPercent: 0 })
          setPortfolioFromManual(true)
        } else {
          setPortfolio({ totalValue: 15250000, totalProfit: 1250000, profitPercent: 8.93 })
        }
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

      {apiFailed && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          백엔드에 연결할 수 없어 기본 데이터를 표시합니다. 로컬에서 백엔드(localhost:8000)가 실행 중인지 확인하세요.
        </div>
      )}

      {/* 주요 지수 카드 */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">주요 지수</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(Array.isArray(indices) ? indices : []).map((index) => {
            const val = Number(index?.value) || 0
            const ch = Number(index?.change) ?? 0
            const chPct = Number(index?.changePercent) ?? 0
            return (
            <div key={index?.name ?? index} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-500">{index?.name ?? '-'}</p>
                  <p className="text-2xl font-bold mt-1">{val.toLocaleString()}</p>
                </div>
                <div className={`p-2 rounded-lg ${ch >= 0 ? 'bg-up' : 'bg-down'}`}>
                  {ch >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-red-500" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-blue-500" />
                  )}
                </div>
              </div>
              <div className="mt-4 flex justify-between items-center">
                <span className={ch >= 0 ? 'text-up' : 'text-down'}>
                  {ch >= 0 ? '+' : ''}{ch.toFixed(2)} ({chPct.toFixed(2)}%)
                </span>
                <button
                  onClick={() => openChart(index?.name ?? '')}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <BarChart2 className="w-4 h-4" />
                  차트
                </button>
              </div>
            </div>
          );
          })}
        </div>
      </div>

      {/* 원자재 & 해외 지수 */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">원자재 & 해외 지수</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(Array.isArray(commodities) ? commodities : []).map((item) => {
            const val = Number(item?.value) || 0
            const ch = Number(item?.change) ?? 0
            const chPct = Number(item?.changePercent) ?? 0
            const name = item?.name ?? '-'
            const isDollar = name === '금' || name === '은' || name === '구리'
            return (
            <div key={name} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-500">{name}</p>
                  <p className="text-xl font-bold mt-1">
                    {isDollar ? `$${val.toLocaleString()}` : val.toLocaleString()}
                  </p>
                </div>
                <div className={`p-1.5 rounded-lg ${ch >= 0 ? 'bg-up' : 'bg-down'}`}>
                  {ch >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-red-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-blue-500" />
                  )}
                </div>
              </div>
              <div className="mt-3 flex justify-between items-center">
                <span className={`text-sm ${ch >= 0 ? 'text-up' : 'text-down'}`}>
                  {ch >= 0 ? '+' : ''}{chPct.toFixed(2)}%
                </span>
                <button
                  onClick={() => openChart(name)}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <BarChart2 className="w-3 h-3" />
                  차트
                </button>
              </div>
            </div>
          );
          })}
        </div>
      </div>

      {/* 포트폴리오 요약 */}
      {portfolio && (
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <h2 className="text-lg font-semibold text-gray-800">내 포트폴리오</h2>
            {portfolioFromManual && (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 text-sm text-green-700 bg-green-50 px-3 py-1.5 rounded-lg">
                  <CheckCircle className="w-4 h-4" />
                  내 계좌 연동됨
                </span>
                <Link to="/portfolio" className="text-sm text-primary-600 hover:underline">
                  포트폴리오에서 수정
                </Link>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary-50 rounded-lg">
                <DollarSign className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">총 평가금액</p>
                <p className="text-2xl font-bold">{(Number(portfolio?.totalValue) || 0).toLocaleString()}원</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${(Number(portfolio?.totalProfit) ?? 0) >= 0 ? 'bg-up' : 'bg-down'}`}>
                <Activity className={`w-6 h-6 ${(Number(portfolio?.totalProfit) ?? 0) >= 0 ? 'text-red-500' : 'text-blue-500'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">총 수익</p>
                <p className={`text-2xl font-bold ${(Number(portfolio?.totalProfit) ?? 0) >= 0 ? 'text-up' : 'text-down'}`}>
                  {(Number(portfolio?.totalProfit) ?? 0) >= 0 ? '+' : ''}{(Number(portfolio?.totalProfit) || 0).toLocaleString()}원
                  <span className="text-base ml-2">({(Number(portfolio?.profitPercent) ?? 0).toFixed(2)}%)</span>
                </p>
              </div>
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
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold text-lg">{chartModal.name} 차트</h3>
              <button
                onClick={closeChart}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              {chartError ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg border">
                  <p className="text-gray-600 mb-2">차트 이미지를 불러올 수 없습니다</p>
                  <p className="text-sm text-gray-500">아래 버튼을 눌러 네이버 금융에서 확인해주세요</p>
                </div>
              ) : (
                <img 
                  src={`${chartUrls[chartModal.name]}?t=${Date.now()}`}
                  alt={`${chartModal.name} 차트`}
                  className="w-full rounded-lg border"
                  onError={() => setChartError(true)}
                />
              )}
              <div className="mt-4 flex gap-2">
                <a
                  href={detailUrls[chartModal.name]}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 btn-primary text-center"
                >
                  네이버 금융에서 상세보기
                </a>
                <button
                  onClick={closeChart}
                  className="btn-secondary"
                >
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
