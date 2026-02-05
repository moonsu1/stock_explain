/**
 * 타입 정의
 */

// 지수 데이터
export interface IndexData {
  name: string
  value: number
  change: number
  changePercent: number
}

// 종목 정보
export interface StockInfo {
  code: string
  name: string
  currentPrice: number
  change: number
  changePercent: number
  volume: number
}

// 계좌 정보
export interface AccountInfo {
  accountNo: string
  totalDeposit: number
  totalEvaluation: number
  totalProfit: number
  profitPercent: number
}

// 보유 종목
export interface HoldingStock {
  code: string
  name: string
  quantity: number
  avgPrice: number
  currentPrice: number
  profit: number
  profitPercent: number
}

// 포트폴리오 요약
export interface PortfolioSummary {
  totalValue: number
  totalProfit: number
  profitPercent: number
}

// 뉴스 아이템
export interface NewsItem {
  title: string
  source: string
  time: string
  url: string
  summary?: string
}

// 유망 테마
export interface HotTheme {
  name: string
  reason: string
  kospiLeader: string
  kosdaqLeader: string
}

// 기술적 지표 요약
export interface TechnicalSummary {
  overall: string
  avgRsi: number
  rsiStatus: string
  bollingerStatus: string
  maStatus: string
  oversoldStocks: string[]
  overboughtStocks: string[]
}

// 시황 분석 (확장 버전)
export interface MarketAnalysis {
  summary: string
  newsAnalysis: string
  kospiAnalysis: string
  kosdaqAnalysis: string
  nasdaqAnalysis: string
  technicalSummary: TechnicalSummary
  marketSentiment: string
  hotThemes: HotTheme[]
  riskFactors: string[]
  actionItems: string[]
  recommendation: string
  generatedAt: string
}

// 매매 전략
export interface TradingStrategy {
  id: string
  name: string
  enabled: boolean
  stockCode: string
  stockName: string
  buyConditions: StrategyCondition[]
  sellConditions: StrategyCondition[]
  maxAmount: number
  lossCutPercent: number
  profitTakePercent: number
}

export interface StrategyCondition {
  type: string
  value: number
}

// 거래 기록
export interface TradeRecord {
  id: string
  timestamp: string
  orderType: 'buy' | 'sell'
  stockCode: string
  stockName: string
  quantity: number
  price: number
  reason: string
  strategyId: string
}

// 시장 상태
export interface MarketStatus {
  isOpen: boolean
  status: string
  currentTime: string
  openTime: string
  closeTime: string
}
