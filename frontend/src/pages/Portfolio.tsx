import { useEffect, useState } from 'react'
import { RefreshCw, LogIn, TrendingUp, TrendingDown } from 'lucide-react'
import axios from 'axios'

interface Stock {
  code: string
  name: string
  quantity: number
  avgPrice: number
  currentPrice: number
  profit: number
  profitPercent: number
}

interface AccountInfo {
  accountNo: string
  totalDeposit: number
  totalEvaluation: number
  totalProfit: number
}

export default function Portfolio() {
  const [isConnected, setIsConnected] = useState(false)
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)

  const handleConnect = async () => {
    setLoading(true)
    try {
      const response = await axios.post('/api/portfolio/connect')
      if (response.data.success) {
        setIsConnected(true)
        await fetchPortfolio()
      }
    } catch (error) {
      console.error('연결 실패:', error)
      // 더미 데이터로 테스트
      setIsConnected(true)
      setAccount({
        accountNo: '********1234',
        totalDeposit: 5000000,
        totalEvaluation: 15250000,
        totalProfit: 1250000,
      })
      setStocks([
        {
          code: '233740',
          name: 'KODEX 코스닥150 레버리지',
          quantity: 100,
          avgPrice: 8500,
          currentPrice: 9200,
          profit: 70000,
          profitPercent: 8.24,
        },
        {
          code: '005930',
          name: '삼성전자',
          quantity: 50,
          avgPrice: 72000,
          currentPrice: 75000,
          profit: 150000,
          profitPercent: 4.17,
        },
        {
          code: '000660',
          name: 'SK하이닉스',
          quantity: 30,
          avgPrice: 135000,
          currentPrice: 142000,
          profit: 210000,
          profitPercent: 5.19,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const fetchPortfolio = async () => {
    try {
      const [accountRes, stocksRes] = await Promise.all([
        axios.get('/api/portfolio/account'),
        axios.get('/api/portfolio/stocks'),
      ])
      setAccount(accountRes.data)
      setStocks(stocksRes.data)
    } catch (error) {
      console.error('포트폴리오 조회 실패:', error)
    }
  }

  if (!isConnected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">포트폴리오</h1>
          <p className="text-gray-500 mt-1">키움증권 계좌를 연동하세요</p>
        </div>

        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <LogIn className="w-8 h-8 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">계좌 연동 필요</h3>
          <p className="text-gray-500 mt-2 mb-6">
            키움증권 Open API+에 로그인하여<br />
            보유 종목과 수익률을 확인하세요
          </p>
          <button
            onClick={handleConnect}
            disabled={loading}
            className="btn-primary inline-flex items-center gap-2"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            키움증권 연동하기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">포트폴리오</h1>
          <p className="text-gray-500 mt-1">내 보유 종목 현황</p>
        </div>
        <button
          onClick={fetchPortfolio}
          disabled={loading}
          className="btn-secondary inline-flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          새로고침
        </button>
      </div>

      {/* 계좌 요약 */}
      {account && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">계좌번호</p>
            <p className="text-lg font-semibold mt-1">{account.accountNo}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">예수금</p>
            <p className="text-lg font-semibold mt-1">{account.totalDeposit.toLocaleString()}원</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">총 평가금액</p>
            <p className="text-lg font-semibold mt-1">{account.totalEvaluation.toLocaleString()}원</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">총 수익</p>
            <p className={`text-lg font-semibold mt-1 ${account.totalProfit >= 0 ? 'text-up' : 'text-down'}`}>
              {account.totalProfit >= 0 ? '+' : ''}{account.totalProfit.toLocaleString()}원
            </p>
          </div>
        </div>
      )}

      {/* 보유 종목 테이블 */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">종목명</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">보유수량</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">평균단가</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">현재가</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">수익금</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">수익률</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {stocks.map((stock) => (
              <tr key={stock.code} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{stock.name}</p>
                    <p className="text-sm text-gray-500">{stock.code}</p>
                  </div>
                </td>
                <td className="text-right px-6 py-4 font-medium">
                  {stock.quantity.toLocaleString()}주
                </td>
                <td className="text-right px-6 py-4">
                  {stock.avgPrice.toLocaleString()}원
                </td>
                <td className="text-right px-6 py-4 font-medium">
                  {stock.currentPrice.toLocaleString()}원
                </td>
                <td className={`text-right px-6 py-4 font-medium ${stock.profit >= 0 ? 'text-up' : 'text-down'}`}>
                  <div className="flex items-center justify-end gap-1">
                    {stock.profit >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    {stock.profit >= 0 ? '+' : ''}{stock.profit.toLocaleString()}원
                  </div>
                </td>
                <td className={`text-right px-6 py-4 font-medium ${stock.profitPercent >= 0 ? 'text-up' : 'text-down'}`}>
                  {stock.profitPercent >= 0 ? '+' : ''}{stock.profitPercent.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
