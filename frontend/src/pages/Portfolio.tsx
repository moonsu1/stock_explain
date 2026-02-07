import { useState, useEffect } from 'react'
import { RefreshCw, LogIn, TrendingUp, TrendingDown, Edit3, Save, CheckCircle } from 'lucide-react'
import axios from 'axios'
import { getSavedPortfolio, setSavedPortfolio, type SavedPortfolio } from '../utils/portfolioStorage'

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
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [showManualForm, setShowManualForm] = useState(false)
  const [manualForm, setManualForm] = useState({
    totalValue: 0,
    totalProfit: 0,
    profitPercent: 0,
    accountNo: '',
    totalDeposit: 0,
  })
  const [isFromSaved, setIsFromSaved] = useState(false)

  useEffect(() => {
    const saved = getSavedPortfolio()
    if (saved) {
      setAccount({
        accountNo: saved.accountNo ?? '직접 입력',
        totalDeposit: saved.totalDeposit ?? 0,
        totalEvaluation: saved.totalValue,
        totalProfit: saved.totalProfit,
      })
      setManualForm({
        totalValue: saved.totalValue,
        totalProfit: saved.totalProfit,
        profitPercent: saved.profitPercent,
        accountNo: saved.accountNo ?? '',
        totalDeposit: saved.totalDeposit ?? 0,
      })
      setIsFromSaved(true)
    }
  }, [])

  useEffect(() => {
    if (account) fetchStocks()
  }, [account])

  const handleConnect = async () => {
    setLoading(true)
    try {
      const res = await axios.post('/api/portfolio/connect')
      if (res.data.success) {
        const [accRes, stRes] = await Promise.all([
          axios.get('/api/portfolio/account'),
          axios.get('/api/portfolio/stocks'),
        ])
        setAccount(accRes?.data ?? null)
        setStocks(Array.isArray(stRes?.data) ? stRes.data : [])
        setIsFromSaved(false)
      }
    } catch (e) {
      console.error('연결 실패:', e)
      const status = axios.isAxiosError(e) ? e.response?.status : null
      if (status === 405) {
        alert('백엔드 연결 오류(405). Vercel 환경 변수 BACKEND_URL과 백엔드(Railway 등) 서버가 동작 중인지 확인하세요.')
      }
      const [accRes, stRes] = await Promise.all([
        axios.get('/api/portfolio/account').catch(() => ({ data: null })),
        axios.get('/api/portfolio/stocks').catch(() => ({ data: [] })),
      ])
      if (accRes?.data != null) setAccount(accRes.data)
      setStocks(Array.isArray(stRes?.data) ? stRes.data : [])
    } finally {
      setLoading(false)
    }
  }

  const fetchStocks = async () => {
    try {
      const res = await axios.get<Stock[]>('/api/portfolio/stocks')
      setStocks(Array.isArray(res?.data) ? res.data : [])
    } catch {
      setStocks([])
    }
  }

  const handleSaveManual = () => {
    const totalValue = manualForm.totalValue || 0
    const totalProfit = manualForm.totalProfit || 0
    const profitPercent =
      totalValue && totalValue !== totalProfit
        ? (totalProfit / (totalValue - totalProfit)) * 100
        : manualForm.profitPercent
    const data: SavedPortfolio = {
      totalValue,
      totalProfit,
      profitPercent,
      accountNo: manualForm.accountNo || undefined,
      totalDeposit: manualForm.totalDeposit || undefined,
    }
    setSavedPortfolio(data)
    setAccount({
      accountNo: manualForm.accountNo || '직접 입력',
      totalDeposit: manualForm.totalDeposit ?? 0,
      totalEvaluation: totalValue,
      totalProfit,
    })
    setIsFromSaved(true)
    setShowManualForm(false)
  }

  const handleSaveAsMyAccount = () => {
    if (!account) return
    setSavedPortfolio({
      totalValue: account.totalEvaluation,
      totalProfit: account.totalProfit,
      profitPercent:
        account.totalEvaluation && account.totalEvaluation !== account.totalProfit
          ? (account.totalProfit / (account.totalEvaluation - account.totalProfit)) * 100
          : 0,
      accountNo: account.accountNo,
      totalDeposit: account.totalDeposit,
    })
    setIsFromSaved(true)
  }

  const hasAccount = account !== null

  if (!hasAccount && !showManualForm) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">포트폴리오</h1>
          <p className="text-gray-500 mt-1">키움증권 계좌를 연동하거나 직접 입력하세요</p>
        </div>
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <LogIn className="w-8 h-8 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">계좌 연동</h3>
          <p className="text-gray-500 mt-2 mb-6">
            키움증권 Open API+로 연동하거나,<br />
            총 평가금액·수익을 직접 입력해 저장할 수 있어요.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={handleConnect}
              disabled={loading}
              className="btn-primary inline-flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              키움증권 연동하기
            </button>
            <button
              onClick={() => setShowManualForm(true)}
              className="btn-secondary inline-flex items-center justify-center gap-2"
            >
              <Edit3 className="w-4 h-4" />
              계좌 정보 직접 입력
            </button>
          </div>
        </div>

        {showManualForm && (
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">계좌 정보 직접 입력</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">총 평가금액 (원)</label>
                <input
                  type="number"
                  value={manualForm.totalValue || ''}
                  onChange={(e) => setManualForm((p) => ({ ...p, totalValue: Number(e.target.value) || 0 }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">총 수익 (원)</label>
                <input
                  type="number"
                  value={manualForm.totalProfit || ''}
                  onChange={(e) => setManualForm((p) => ({ ...p, totalProfit: Number(e.target.value) || 0 }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">수익률 (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={manualForm.profitPercent || ''}
                  onChange={(e) => setManualForm((p) => ({ ...p, profitPercent: Number(e.target.value) || 0 }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">예수금 (원, 선택)</label>
                <input
                  type="number"
                  value={manualForm.totalDeposit || ''}
                  onChange={(e) => setManualForm((p) => ({ ...p, totalDeposit: Number(e.target.value) || 0 }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                  placeholder="0"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-gray-600 mb-1">계좌번호 (선택)</label>
                <input
                  type="text"
                  value={manualForm.accountNo}
                  onChange={(e) => setManualForm((p) => ({ ...p, accountNo: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                  placeholder=""
                />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={handleSaveManual} className="btn-primary inline-flex items-center gap-2">
                <Save className="w-4 h-4" />
                저장 후 연동
              </button>
              <button onClick={() => setShowManualForm(false)} className="btn-secondary">
                취소
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">포트폴리오</h1>
          <p className="text-gray-500 mt-1">내 보유 종목 현황</p>
        </div>
        <div className="flex items-center gap-2">
          {isFromSaved && (
            <span className="inline-flex items-center gap-1 text-sm text-green-700 bg-green-50 px-3 py-1.5 rounded-lg">
              <CheckCircle className="w-4 h-4" />
              내 계정 연동됨
            </span>
          )}
          <button onClick={fetchStocks} disabled={loading} className="btn-secondary inline-flex items-center gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
          <button onClick={() => setShowManualForm(true)} className="btn-secondary inline-flex items-center gap-2">
            <Edit3 className="w-4 h-4" />
            직접 입력 수정
          </button>
          {!isFromSaved && account && (
            <button onClick={handleSaveAsMyAccount} className="btn-primary inline-flex items-center gap-2">
              <Save className="w-4 h-4" />
              내 계정으로 저장
            </button>
          )}
        </div>
      </div>

      {showManualForm && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">계좌 정보 수정</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">총 평가금액 (원)</label>
              <input
                type="number"
                value={manualForm.totalValue || ''}
                onChange={(e) => setManualForm((p) => ({ ...p, totalValue: Number(e.target.value) || 0 }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">총 수익 (원)</label>
              <input
                type="number"
                value={manualForm.totalProfit || ''}
                onChange={(e) => setManualForm((p) => ({ ...p, totalProfit: Number(e.target.value) || 0 }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">수익률 (%)</label>
              <input
                type="number"
                step="0.01"
                value={manualForm.profitPercent || ''}
                onChange={(e) => setManualForm((p) => ({ ...p, profitPercent: Number(e.target.value) || 0 }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">예수금 (원)</label>
              <input
                type="number"
                value={manualForm.totalDeposit || ''}
                onChange={(e) => setManualForm((p) => ({ ...p, totalDeposit: Number(e.target.value) || 0 }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-gray-600 mb-1">계좌번호</label>
              <input
                type="text"
                value={manualForm.accountNo}
                onChange={(e) => setManualForm((p) => ({ ...p, accountNo: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={handleSaveManual} className="btn-primary inline-flex items-center gap-2">
              <Save className="w-4 h-4" />
              저장
            </button>
            <button onClick={() => setShowManualForm(false)} className="btn-secondary">
              취소
            </button>
          </div>
        </div>
      )}

      {account && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">계좌번호</p>
            <p className="text-lg font-semibold mt-1">{account.accountNo}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">예수금</p>
            <p className="text-lg font-semibold mt-1">{(Number(account?.totalDeposit) || 0).toLocaleString()}원</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">총 평가금액</p>
            <p className="text-lg font-semibold mt-1">{(Number(account?.totalEvaluation) || 0).toLocaleString()}원</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">총 수익</p>
            <p className={`text-lg font-semibold mt-1 ${(Number(account?.totalProfit) ?? 0) >= 0 ? 'text-up' : 'text-down'}`}>
              {(Number(account?.totalProfit) ?? 0) >= 0 ? '+' : ''}{(Number(account?.totalProfit) || 0).toLocaleString()}원
            </p>
          </div>
        </div>
      )}

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
            {(Array.isArray(stocks) ? stocks : []).map((stock, idx) => {
              const qty = Number(stock?.quantity) ?? 0
              const avg = Number(stock?.avgPrice) ?? 0
              const cur = Number(stock?.currentPrice) ?? 0
              const profit = Number(stock?.profit) ?? 0
              const pct = Number(stock?.profitPercent) ?? 0
              return (
              <tr key={stock?.code ?? stock?.name ?? idx} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{stock?.name ?? '-'}</p>
                    <p className="text-sm text-gray-500">{stock?.code ?? ''}</p>
                  </div>
                </td>
                <td className="text-right px-6 py-4 font-medium">{qty.toLocaleString()}주</td>
                <td className="text-right px-6 py-4">{avg.toLocaleString()}원</td>
                <td className="text-right px-6 py-4 font-medium">{cur.toLocaleString()}원</td>
                <td className={`text-right px-6 py-4 font-medium ${profit >= 0 ? 'text-up' : 'text-down'}`}>
                  <div className="flex items-center justify-end gap-1">
                    {profit >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {profit >= 0 ? '+' : ''}{profit.toLocaleString()}원
                  </div>
                </td>
                <td className={`text-right px-6 py-4 font-medium ${pct >= 0 ? 'text-up' : 'text-down'}`}>
                  {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                </td>
              </tr>
            )})}
          </tbody>
        </table>
        {(Array.isArray(stocks) ? stocks : []).length === 0 && (
          <div className="py-12 text-center text-gray-500">보유 종목이 없거나 API에서 가져올 수 없습니다.</div>
        )}
      </div>
    </div>
  )
}
