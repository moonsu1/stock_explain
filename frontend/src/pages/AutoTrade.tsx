import { useState } from 'react'
import { Bot, Play, Pause, Settings, AlertTriangle, History } from 'lucide-react'
import clsx from 'clsx'

interface Strategy {
  id: string
  name: string
  description: string
  enabled: boolean
  stockCode: string
  stockName: string
  buyCondition: string
  sellCondition: string
  maxAmount: number
}

interface TradeHistory {
  id: string
  time: string
  type: 'buy' | 'sell'
  stockName: string
  quantity: number
  price: number
  reason: string
}

export default function AutoTrade() {
  const [isRunning, setIsRunning] = useState(false)
  const [strategies, setStrategies] = useState<Strategy[]>([
    {
      id: '1',
      name: 'KODEX 코스닥150 레버리지 전략',
      description: 'RSI + 이동평균선 기반 매매',
      enabled: true,
      stockCode: '233740',
      stockName: 'KODEX 코스닥150 레버리지',
      buyCondition: 'RSI 30 이하 & 5일선 돌파',
      sellCondition: 'RSI 70 이상 또는 -3% 손절',
      maxAmount: 1000000,
    },
  ])
  const [history] = useState<TradeHistory[]>([
    { id: '1', time: '2024-02-05 14:23:15', type: 'buy', stockName: 'KODEX 코스닥150 레버리지', quantity: 50, price: 9150, reason: 'RSI 28 도달, 매수 신호' },
    { id: '2', time: '2024-02-04 10:05:32', type: 'sell', stockName: 'KODEX 코스닥150 레버리지', quantity: 30, price: 9380, reason: 'RSI 72 도달, 매도 신호' },
  ])
  const [_showNewStrategy, _setShowNewStrategy] = useState(false)

  const toggleRunning = () => {
    setIsRunning(!isRunning)
  }

  const toggleStrategy = (id: string) => {
    setStrategies(strategies.map(s => 
      s.id === id ? { ...s, enabled: !s.enabled } : s
    ))
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">자동매매</h1>
          <p className="text-gray-500 mt-1">전략 기반 자동 주문 시스템</p>
        </div>
        <button
          onClick={toggleRunning}
          className={clsx(
            'inline-flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors',
            isRunning
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'bg-green-500 text-white hover:bg-green-600'
          )}
        >
          {isRunning ? (
            <>
              <Pause className="w-5 h-5" />
              자동매매 중지
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              자동매매 시작
            </>
          )}
        </button>
      </div>

      {/* 경고 메시지 */}
      <div className="card bg-yellow-50 border-yellow-200">
        <div className="flex gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-yellow-800">자동매매 주의사항</h4>
            <p className="text-sm text-yellow-700 mt-1">
              자동매매는 실제 주문이 체결될 수 있습니다. 반드시 모의투자로 먼저 테스트하시고,
              손실에 대한 책임은 투자자 본인에게 있습니다.
            </p>
          </div>
        </div>
      </div>

      {/* 상태 표시 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-3 h-3 rounded-full',
              isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
            )} />
            <div>
              <p className="text-sm text-gray-500">자동매매 상태</p>
              <p className="font-semibold">{isRunning ? '실행 중' : '중지됨'}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">활성 전략</p>
          <p className="text-2xl font-bold mt-1">
            {strategies.filter(s => s.enabled).length} / {strategies.length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">오늘 체결</p>
          <p className="text-2xl font-bold mt-1">2건</p>
        </div>
      </div>

      {/* 전략 목록 */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold">매매 전략</h3>
          </div>
          <button
            onClick={() => _setShowNewStrategy(true)}
            className="btn-secondary text-sm"
          >
            + 전략 추가
          </button>
        </div>
        
        <div className="space-y-4">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              className={clsx(
                'border rounded-lg p-4 transition-colors',
                strategy.enabled ? 'border-primary-200 bg-primary-50/50' : 'border-gray-200'
              )}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">{strategy.name}</h4>
                    <span className={clsx(
                      'text-xs px-2 py-0.5 rounded-full',
                      strategy.enabled
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    )}>
                      {strategy.enabled ? '활성' : '비활성'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{strategy.description}</p>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                    <div>
                      <p className="text-gray-500">종목</p>
                      <p className="font-medium">{strategy.stockName} ({strategy.stockCode})</p>
                    </div>
                    <div>
                      <p className="text-gray-500">최대 투자금</p>
                      <p className="font-medium">{strategy.maxAmount.toLocaleString()}원</p>
                    </div>
                    <div>
                      <p className="text-gray-500">매수 조건</p>
                      <p className="font-medium text-red-600">{strategy.buyCondition}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">매도 조건</p>
                      <p className="font-medium text-blue-600">{strategy.sellCondition}</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-gray-100 rounded-lg">
                    <Settings className="w-4 h-4 text-gray-500" />
                  </button>
                  <button
                    onClick={() => toggleStrategy(strategy.id)}
                    className={clsx(
                      'relative w-12 h-6 rounded-full transition-colors',
                      strategy.enabled ? 'bg-primary-600' : 'bg-gray-300'
                    )}
                  >
                    <span
                      className={clsx(
                        'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform',
                        strategy.enabled ? 'translate-x-7' : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 매매 이력 */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold">최근 체결 이력</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-3">시간</th>
                <th className="pb-3">구분</th>
                <th className="pb-3">종목</th>
                <th className="pb-3 text-right">수량</th>
                <th className="pb-3 text-right">체결가</th>
                <th className="pb-3">매매 사유</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {history.map((trade) => (
                <tr key={trade.id} className="text-sm">
                  <td className="py-3 text-gray-600">{trade.time}</td>
                  <td className="py-3">
                    <span className={clsx(
                      'px-2 py-1 rounded text-xs font-medium',
                      trade.type === 'buy'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-blue-100 text-blue-700'
                    )}>
                      {trade.type === 'buy' ? '매수' : '매도'}
                    </span>
                  </td>
                  <td className="py-3 font-medium">{trade.stockName}</td>
                  <td className="py-3 text-right">{trade.quantity}주</td>
                  <td className="py-3 text-right">{trade.price.toLocaleString()}원</td>
                  <td className="py-3 text-gray-600">{trade.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
