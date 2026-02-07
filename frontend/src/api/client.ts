/**
 * API 클라이언트
 * Vercel 배포 시 getApiBaseUrl()이 /api/proxy 를 반환해 프록시로 가도록 함.
 * (VITE_API_URL 은 빌드 시에만 주입되므로, Vercel에서 비워두면 '/api'로 떨어져 404 난다.)
 */
import axios, { type AxiosResponse, type AxiosError } from 'axios'
import { getApiBaseUrl } from '../utils/apiBase'

const API_BASE_URL = getApiBaseUrl() || import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// ===== 시장 정보 API =====

export const marketApi = {
  // 주요 지수 조회
  getIndices: () => apiClient.get('/market/indices'),
  
  // 종목 정보 조회
  getStockInfo: (code: string) => apiClient.get(`/market/stock/${code}`),
  
  // 시장 상태 조회
  getMarketStatus: () => apiClient.get('/market/status'),
}

// ===== 포트폴리오 API =====

export const portfolioApi = {
  // 키움증권 연결
  connect: () => apiClient.post('/portfolio/connect'),
  
  // 연결 해제
  disconnect: () => apiClient.post('/portfolio/disconnect'),
  
  // 연결 상태 조회
  getStatus: () => apiClient.get('/portfolio/status'),
  
  // 포트폴리오 요약
  getSummary: () => apiClient.get('/portfolio/summary'),
  
  // 계좌 정보
  getAccount: () => apiClient.get('/portfolio/account'),
  
  // 보유 종목
  getStocks: () => apiClient.get('/portfolio/stocks'),
}

// ===== 시황 분석 API =====

export const analysisApi = {
  // 뉴스 목록
  getNews: () => apiClient.get('/analysis/news'),
  
  // 종목별 뉴스
  getStockNews: (code: string) => apiClient.get(`/analysis/news/stock/${code}`),
  
  // AI 분석 생성
  generateAnalysis: (holdings?: string[]) => 
    apiClient.post('/analysis/generate', { holdings }),
  
  // 지수 조회
  getIndices: () => apiClient.get('/analysis/indices'),
}

// ===== 매매 API =====

export const tradeApi = {
  // 주문 실행
  placeOrder: (data: {
    code: string
    quantity: number
    price?: number
    order_type: 'buy' | 'sell'
  }) => apiClient.post('/trade/order', data),
  
  // 자동매매 상태
  getAutoStatus: () => apiClient.get('/trade/auto/status'),
  
  // 자동매매 시작
  startAuto: () => apiClient.post('/trade/auto/start'),
  
  // 자동매매 중지
  stopAuto: () => apiClient.post('/trade/auto/stop'),
  
  // 전략 목록
  getStrategies: () => apiClient.get('/trade/strategies'),
  
  // 전략 생성
  createStrategy: (data: any) => apiClient.post('/trade/strategies', data),
  
  // 전략 수정
  updateStrategy: (id: string, data: any) => 
    apiClient.put(`/trade/strategies/${id}`, data),
  
  // 전략 삭제
  deleteStrategy: (id: string) => 
    apiClient.delete(`/trade/strategies/${id}`),
  
  // 전략 토글
  toggleStrategy: (id: string) => 
    apiClient.post(`/trade/strategies/${id}/toggle`),
  
  // 거래 이력
  getHistory: (limit = 50) => 
    apiClient.get(`/trade/history?limit=${limit}`),
}

export default {
  market: marketApi,
  portfolio: portfolioApi,
  analysis: analysisApi,
  trade: tradeApi,
}
