import { useEffect, useState, useRef } from 'react'
import { 
  RefreshCw, Newspaper, TrendingUp, TrendingDown, Sparkles, 
  Activity, Target, AlertTriangle, CheckCircle, Flame,
  BarChart3, ArrowUpCircle, ArrowDownCircle, Zap, Coins, ClipboardList
} from 'lucide-react'
import axios from 'axios'
import { getApiBaseForFetch } from '../utils/apiBase'

interface NewsItem {
  title: string
  source: string
  time: string
  url: string
}

interface HotTheme {
  name: string
  reason: string
  kospiLeader: string
  kosdaqLeader: string
}

interface TechnicalSummary {
  overall: string
  avgRsi: number
  rsiStatus: string
  bollingerStatus: string
  maStatus: string
  oversoldStocks: string[]
  overboughtStocks: string[]
}

interface MarketAnalysis {
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
  commoditiesAnalysis?: string
  holdingsStrategy?: string
  isMock?: boolean
}

// 시장 심리 색상
const sentimentColors: Record<string, string> = {
  '공포': 'bg-red-100 text-red-700 border-red-200',
  '불안': 'bg-orange-100 text-orange-700 border-orange-200',
  '중립': 'bg-gray-100 text-gray-700 border-gray-200',
  '낙관': 'bg-green-100 text-green-700 border-green-200',
  '탐욕': 'bg-emerald-100 text-emerald-700 border-emerald-200',
}

// RSI 게이지 색상
const getRsiColor = (rsi: number) => {
  if (rsi >= 70) return 'text-red-500'
  if (rsi <= 30) return 'text-blue-500'
  if (rsi >= 60) return 'text-orange-500'
  if (rsi <= 40) return 'text-cyan-500'
  return 'text-gray-500'
}

/** 종목별 전망/전략 카드용 */
export interface HoldingCard {
  name: string
  outlook: string
  strategy: string
}

/** 보유 종목 전략 텍스트/JSON을 종목별 카드 배열로 파싱. 파싱 실패 시 null */
function parseHoldingsStrategy(raw: string | Record<string, unknown> | null | undefined): HoldingCard[] | null {
  if (raw == null) return null
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    const entries = Object.entries(raw)
    if (entries.length === 0) return null
    const cards: HoldingCard[] = entries.map(([name, v]) => {
      if (typeof v === 'string') {
        const s = v.trim()
        const outlookMatch = s.match(/(?:전망|outlook)\s*[：:]?\s*([^\n]+)/i)
        const strategyMatch = s.match(/(?:전략|strategy)\s*[：:]?\s*([^\n]+)/i)
        return {
          name: name.trim(),
          outlook: outlookMatch ? outlookMatch[1].trim() : s,
          strategy: strategyMatch ? strategyMatch[1].trim() : '',
        }
      }
      const o = (v as Record<string, unknown>) ?? {}
      const outlook = String(o.전망 ?? o.outlook ?? '')
      const strategy = String(o.전략 ?? o.strategy ?? '')
      return { name: name.trim(), outlook, strategy }
    })
    return cards.length > 0 ? cards : null
  }
  const str = typeof raw === 'string' ? raw.trim() : ''
  if (!str) return null
  try {
    if (str.startsWith('{')) {
      const obj = JSON.parse(str) as Record<string, unknown>
      return parseHoldingsStrategy(obj)
    }
  } catch {
    // ignore
  }
  const cards: HoldingCard[] = []
  const codeInParen = /\([A-Za-z0-9]+\)/
  const extractBlock = (block: string): HoldingCard | null => {
    const trimmed = block.trim()
    if (!trimmed) return null
    const firstLine = trimmed.split('\n')[0] ?? ''
    const name = firstLine.replace(/^###\s*/, '').replace(/^\*\*/, '').replace(/\*\*$/, '').trim()
    if (!name || !codeInParen.test(name)) return null
    const body = trimmed.includes('\n') ? trimmed.slice(trimmed.indexOf('\n') + 1) : ''
    const outlookMatch = body.match(/(?:\*\*전망\*\*|전망)\s*[：:]?\s*([^\n]+(?:\n(?!\s*[-*]\s*\*\*전략|\n\*\*[^\n]+\([A-Za-z0-9]+\))[^\n]*)*)/i)
    const strategyMatch = body.match(/(?:\*\*전략\*\*|전략)\s*[：:]?\s*([^\n]+(?:\n(?!\s*[-*]\s*\*\*[^\n]*전망|\n\*\*[^\n]+\([A-Za-z0-9]+\))[^\n]*)*)/i)
    const outlook = outlookMatch ? outlookMatch[1].replace(/\n/g, ' ').trim() : ''
    const strategy = strategyMatch ? strategyMatch[1].replace(/\n/g, ' ').trim() : ''
    if (outlook || strategy) return { name, outlook, strategy }
    return null
  }
  // 실시간: ### 종목(코드) 또는 **종목(코드)** 로 구분된 블록 (코드: 숫자 또는 영문+숫자)
  const blockSplitters = [
    /(?=###\s[^\n]+\([A-Za-z0-9]+\))/,
    /(?=\n\*\*[^\n]*?\([A-Za-z0-9]+\)\*\*)/,
    /(?=\n\n[^\n]+\([A-Za-z0-9]+\)\s*\n)/,
  ]
  for (const re of blockSplitters) {
    const parts = str.split(re).filter((s) => s.trim().length > 0)
    if (parts.length >= 2 || (parts.length === 1 && codeInParen.test(parts[0]))) {
      for (const part of parts) {
        const card = extractBlock(part)
        if (card) cards.push(card)
      }
      if (cards.length > 0) return cards
    }
    cards.length = 0
  }
  const singleBlock = /^([^\n]+\([A-Za-z0-9]+\))\s*\n([\s\S]*)/m.exec(str)
  if (singleBlock) {
    const body = singleBlock[2]
    const outlookMatch = body.match(/(?:\*\*?전망\*\*?|전망)\s*[：:]?\s*([^\n]+)/i)
    const strategyMatch = body.match(/(?:\*\*?전략\*\*?|전략)\s*[：:]?\s*([^\n]+)/i)
    cards.push({
      name: singleBlock[1].replace(/\*\*/g, '').trim(),
      outlook: outlookMatch ? outlookMatch[1].trim() : '',
      strategy: strategyMatch ? strategyMatch[1].trim() : '',
    })
  }
  if (cards.length === 0 && codeInParen.test(str) && /전망|전략/i.test(str)) {
    const boldNameBlocks = str.split(/(\*\*[^*]+?\([A-Za-z0-9]+\)\*\*)/)
    for (let i = 1; i < boldNameBlocks.length; i += 2) {
      const name = boldNameBlocks[i].replace(/\*\*/g, '').trim()
      const body = boldNameBlocks[i + 1] ?? ''
      const outlookMatch = body.match(/(?:\*\*?전망\*\*?|전망)\s*[：:]?\s*([^\n]+)/i)
      const strategyMatch = body.match(/(?:\*\*?전략\*\*?|전략)\s*[：:]?\s*([^\n]+)/i)
      if (name) cards.push({ name, outlook: outlookMatch ? outlookMatch[1].trim() : '', strategy: strategyMatch ? strategyMatch[1].trim() : '' })
    }
  }
  return cards.length > 0 ? cards : null
}

// 스트리밍 섹션 타입
interface StreamingSections {
  summary: string
  sentiment: string
  kospiAnalysis: string
  kosdaqAnalysis: string
  nasdaqAnalysis: string
  technicalAnalysis: string
  commoditiesAnalysis: string
  holdingsStrategy: string
  theme1: { name: string; content: string }
  theme2: { name: string; content: string }
  theme3: { name: string; content: string }
  riskFactors: string
  recommendation: string
}

const initialSections: StreamingSections = {
  summary: '',
  sentiment: '',
  kospiAnalysis: '',
  kosdaqAnalysis: '',
  nasdaqAnalysis: '',
  technicalAnalysis: '',
  commoditiesAnalysis: '',
  holdingsStrategy: '',
  theme1: { name: '', content: '' },
  theme2: { name: '', content: '' },
  theme3: { name: '', content: '' },
  riskFactors: '',
  recommendation: ''
}

/** 구조화 분석 응답 정규화: snake_case도 camelCase로 통일, 누락 필드 기본값으로 흰화면/크래시 방지 */
function normalizeAnalysisResponse(data: Record<string, unknown> | null): MarketAnalysis | null {
  if (!data || typeof data !== 'object') return null
  const get = (camel: string, snake: string) =>
    (data[camel] ?? data[snake]) as string | undefined
  const tech = (data.technicalSummary ?? data.technical_summary) as Record<string, unknown> | undefined
  const safeTech: TechnicalSummary = tech
    ? {
        overall: String(tech.overall ?? ''),
        avgRsi: Number(tech.avgRsi ?? tech.avg_rsi ?? 50),
        rsiStatus: String(tech.rsiStatus ?? tech.rsi_status ?? ''),
        bollingerStatus: String(tech.bollingerStatus ?? tech.bollinger_status ?? ''),
        maStatus: String(tech.maStatus ?? tech.ma_status ?? ''),
        oversoldStocks: Array.isArray(tech.oversoldStocks ?? tech.oversold_stocks) ? (tech.oversoldStocks ?? tech.oversold_stocks) as string[] : [],
        overboughtStocks: Array.isArray(tech.overboughtStocks ?? tech.overbought_stocks) ? (tech.overboughtStocks ?? tech.overbought_stocks) as string[] : [],
      }
    : {
        overall: '', avgRsi: 50, rsiStatus: '', bollingerStatus: '', maStatus: '',
        oversoldStocks: [], overboughtStocks: [],
      }
  const holdingsRaw = data.holdingsStrategy ?? data.holdings_strategy
  let holdingsStrategy = ''
  if (typeof holdingsRaw === 'string') {
    holdingsStrategy = holdingsRaw
  } else if (holdingsRaw != null && typeof holdingsRaw === 'object') {
    const o = holdingsRaw as Record<string, unknown>
    if (typeof o.text === 'string') holdingsStrategy = o.text
    else if (typeof o.content === 'string') holdingsStrategy = o.content
    else if (typeof o.message === 'string') holdingsStrategy = o.message
    else if (Array.isArray(o) && o.every((x) => typeof x === 'string')) holdingsStrategy = (o as string[]).join('\n')
    else if (Array.isArray(o)) holdingsStrategy = (o as unknown[]).map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join('\n')
    else {
      // 객체인데 위에 해당 없으면, 값 중 첫 번째 문자열 사용 또는 예쁘게 JSON 출력
      const firstStr = Object.values(o).find((v) => typeof v === 'string') as string | undefined
      holdingsStrategy = firstStr ?? JSON.stringify(o, null, 2)
    }
  }
  const hotThemesRaw = data.hotThemes ?? data.hot_themes
  const hotThemes: HotTheme[] = Array.isArray(hotThemesRaw)
    ? hotThemesRaw.map((t: Record<string, unknown>) => ({
        name: String(t.name ?? ''),
        reason: String(t.reason ?? ''),
        kospiLeader: String(t.kospiLeader ?? t.kospi_leader ?? ''),
        kosdaqLeader: String(t.kosdaqLeader ?? t.kosdaq_leader ?? ''),
      }))
    : []
  return {
    summary: String(get('summary', 'summary') ?? ''),
    newsAnalysis: String(get('newsAnalysis', 'news_analysis') ?? ''),
    kospiAnalysis: String(get('kospiAnalysis', 'kospi_analysis') ?? ''),
    kosdaqAnalysis: String(get('kosdaqAnalysis', 'kosdaq_analysis') ?? ''),
    nasdaqAnalysis: String(get('nasdaqAnalysis', 'nasdaq_analysis') ?? ''),
    technicalSummary: safeTech,
    marketSentiment: String(get('marketSentiment', 'market_sentiment') ?? '중립'),
    commoditiesAnalysis: String(get('commoditiesAnalysis', 'commodities_analysis') ?? ''),
    holdingsStrategy,
    hotThemes,
    riskFactors: Array.isArray(data.riskFactors ?? data.risk_factors) ? (data.riskFactors ?? data.risk_factors) as string[] : [],
    actionItems: Array.isArray(data.actionItems ?? data.action_items) ? (data.actionItems ?? data.action_items) as string[] : [],
    recommendation: String(get('recommendation', 'recommendation') ?? ''),
    generatedAt: String(get('generatedAt', 'generated_at') ?? ''),
    isMock: Boolean(data.isMock),
  }
}

export default function Analysis() {
  const [news, setNews] = useState<NewsItem[]>([])
  const [analysis, setAnalysis] = useState<MarketAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  
  // 스트리밍 관련 상태
  const [streamingText, setStreamingText] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string>('')
  const streamContainerRef = useRef<HTMLDivElement>(null)
  
  // 구조화된 스트리밍 상태
  const [streamingSections, setStreamingSections] = useState<StreamingSections>(initialSections)
  const [currentSection, setCurrentSection] = useState<string>('')
  // 에러 메시지 (화면에 표시)
  const [analysisError, setAnalysisError] = useState<string>('')
  const [streamError, setStreamError] = useState<string>('')

  useEffect(() => {
    fetchNews()
  }, [])
  
  // 스트리밍 시 자동 스크롤
  useEffect(() => {
    if (streamContainerRef.current && isStreaming) {
      streamContainerRef.current.scrollTop = streamContainerRef.current.scrollHeight
    }
  }, [streamingText, isStreaming])

  const fetchNews = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/analysis/news')
      setNews(Array.isArray(response?.data) ? response.data : [])
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
      setNews([
        { title: '뉴스를 불러오는 중 오류가 발생했습니다', source: '-', time: '-', url: '#' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const generateAnalysis = async () => {
    setAnalysisLoading(true)
    setAnalysisError('')
    try {
      let holdings: { code: string; name: string }[] = []
      try {
        const stocksRes = await axios.get<{ code: string; name?: string }[]>('/api/portfolio/stocks')
        if (Array.isArray(stocksRes.data)) {
          holdings = stocksRes.data
            .filter((s) => s?.code)
            .map((s) => ({ code: s.code, name: s.name ?? s.code }))
        }
      } catch {
        // 보유 종목 없으면 빈 배열로 진행
      }
      const response = await axios.post('/api/analysis/generate', { holdings })
      setAnalysis(normalizeAnalysisResponse(response.data) ?? null)
    } catch (error: unknown) {
      console.error('분석 생성 실패:', error)
      let msg = '분석 생성에 실패했습니다.'
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        if (status === 405) {
          msg = '백엔드 연결 오류(405). Vercel의 BACKEND_URL과 Railway 등 백엔드 서버가 켜져 있는지 확인하세요.'
        } else if (error.response?.data?.detail !== undefined) {
          const d = error.response.data.detail
          msg = Array.isArray(d)
            ? d.map((x: { msg?: string }) => x?.msg || JSON.stringify(x)).join(' ')
            : String(d)
        } else {
          msg = error.message || `요청 실패 (${status ?? '네트워크'})`
        }
      } else if (error instanceof Error) {
        msg = error.message
      }
      setAnalysisError(msg)
    } finally {
      setAnalysisLoading(false)
    }
  }
  
  // 섹션 감지 및 업데이트
  const detectAndUpdateSection = (fullText: string) => {
    const sections: StreamingSections = { ...initialSections }
    
    // 섹션 매핑 (헤더 -> 키) - 더 유연한 패턴
    const sectionMap: { pattern: RegExp; key: keyof StreamingSections; isTheme?: number }[] = [
      { pattern: /##\s*오늘의 시황 요약\s*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'summary' },
      { pattern: /##\s*시장 심리\s*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'sentiment' },
      { pattern: /###?\s*코스피[^\n]*\n([\s\S]*?)(?=\n###?\s|\n##\s|$)/i, key: 'kospiAnalysis' },
      { pattern: /###?\s*코스닥[^\n]*\n([\s\S]*?)(?=\n###?\s|\n##\s|$)/i, key: 'kosdaqAnalysis' },
      { pattern: /###?\s*나스닥[^\n]*\n([\s\S]*?)(?=\n###?\s|\n##\s|$)/i, key: 'nasdaqAnalysis' },
      { pattern: /##\s*기술적 지표[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'technicalAnalysis' },
      { pattern: /##\s*원자재 및 비트코인[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'commoditiesAnalysis' },
      { pattern: /##\s*보유 종목[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'holdingsStrategy' },
      { pattern: /###?\s*1\.\s*([^\n]+)\n([\s\S]*?)(?=\n###?\s*\d|\n##\s|$)/i, key: 'theme1', isTheme: 1 },
      { pattern: /###?\s*2\.\s*([^\n]+)\n([\s\S]*?)(?=\n###?\s*\d|\n##\s|$)/i, key: 'theme2', isTheme: 2 },
      { pattern: /###?\s*3\.\s*([^\n]+)\n([\s\S]*?)(?=\n###?\s*\d|\n##\s|$)/i, key: 'theme3', isTheme: 3 },
      { pattern: /##\s*리스크 요인[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'riskFactors' },
      { pattern: /##\s*투자 전략[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i, key: 'recommendation' },
    ]
    
    for (const { pattern, key, isTheme } of sectionMap) {
      const match = fullText.match(pattern)
      if (match) {
        if (isTheme) {
          const themeKey = key as 'theme1' | 'theme2' | 'theme3'
          sections[themeKey] = { name: match[1]?.trim() || '', content: match[2]?.trim() || '' }
        } else {
          (sections[key] as string) = match[1]?.trim() || ''
        }
      }
    }
    
    // 현재 섹션 감지 (커서 위치용)
    const lastHeader = fullText.match(/##[^#].*$/gm)
    if (lastHeader && lastHeader.length > 0) {
      setCurrentSection(lastHeader[lastHeader.length - 1])
    }
    
    setStreamingSections(sections)
  }
  
  // 스트리밍 분석 생성
  const generateStreamingAnalysis = async () => {
    console.log('[Stream] Starting streaming analysis...')
    setIsStreaming(true)
    setStreamingText('')
    setStreamingSections(initialSections)
    setCurrentSection('')
    setStatusMessage('연결 중...')
    setStreamError('')
    setAnalysis(null)
    
    try {
      let holdings: { code: string; name: string }[] = []
      try {
        const stocksRes = await axios.get<{ code: string; name?: string }[]>('/api/portfolio/stocks')
        if (Array.isArray(stocksRes.data)) {
          holdings = stocksRes.data
            .filter((s) => s?.code)
            .map((s) => ({ code: s.code, name: s.name ?? s.code }))
        }
      } catch {
        // 보유 종목 없으면 빈 배열로 진행
      }
      let apiBase = import.meta.env.VITE_API_URL || ''
      try {
        apiBase = getApiBaseForFetch()
      } catch {
        apiBase = import.meta.env.VITE_API_URL || ''
      }
      // GET + code:name 쿼리 사용 (POST 시 405 나는 환경 회피)
      const holdingsParam = holdings.length
        ? '?holdings=' + encodeURIComponent(holdings.map((h) => `${h.code}:${h.name}`).join(','))
        : ''
      console.log('[Stream] Fetching streaming API, holdings:', holdings.length)
      const response = await fetch(`${apiBase}/api/analysis/generate/stream${holdingsParam}`)
      console.log('[Stream] Response status:', response.status, response.ok)
      
      if (!response.ok) {
        const errMsg = `연결 실패 (${response.status}). 백엔드 URL과 OPENAI_API_KEY를 확인하세요.`
        setStreamError(errMsg)
        throw new Error(errMsg)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('Stream not available')
      }
      
      let buffer = ''
      let fullText = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }
        
        buffer += decoder.decode(value, { stream: true })
        
        // SSE 이벤트 파싱
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6)
            
            if (data === '[DONE]') {
              setIsStreaming(false)
              setStatusMessage('')
              continue
            }
            
            if (data.startsWith('[STATUS]')) {
              setStatusMessage(data.replace('[STATUS] ', ''))
              continue
            }
            
            if (data.startsWith('[ERROR]')) {
              const errMsg = data.replace('[ERROR] ', '').trim()
              setStreamError(errMsg)
              setStatusMessage('')
              setIsStreaming(false)
              continue
            }
            
            // 실제 텍스트 처리
            const text = data.replace(/\\n/g, '\n')
            fullText += text
            setStreamingText(fullText)
            
            // 섹션별 파싱 및 업데이트
            detectAndUpdateSection(fullText)
          }
        }
      }
    } catch (error) {
      console.error('스트리밍 분석 실패:', error)
      setStreamError(error instanceof Error ? error.message : '분석 중 오류가 발생했습니다.')
      setStatusMessage('')
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">시황 분석</h1>
          <p className="text-gray-500 mt-1">AI 기반 전문 시장 분석 리포트</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={generateStreamingAnalysis}
            disabled={isStreaming || analysisLoading}
            className="btn-primary inline-flex items-center gap-2"
          >
            {isStreaming ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {isStreaming ? '분석 중...' : 'AI 실시간 분석'}
          </button>
          <button
            onClick={generateAnalysis}
            disabled={analysisLoading || isStreaming}
            className="btn-secondary inline-flex items-center gap-2"
          >
            {analysisLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {analysisLoading ? '분석 중...' : '구조화 분석'}
          </button>
        </div>
      </div>

      {/* 에러 메시지 표시 */}
      {analysisError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-red-700 text-sm">
          <span className="font-medium">구조화 분석 실패: </span>
          {analysisError}
        </div>
      )}
      {streamError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-red-700 text-sm">
          <span className="font-medium">AI 실시간 분석 오류: </span>
          {streamError}
        </div>
      )}

      {/* 스트리밍 분석 결과 - 구조화된 UI */}
      {(isStreaming || streamingText) && (
        <div className="space-y-6">
          {/* 헤더 + 상태 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="w-6 h-6 text-purple-600" />
              <h2 className="text-lg font-semibold text-purple-900">AI 실시간 분석</h2>
              {isStreaming && (
                <span className="flex items-center gap-1 text-sm text-purple-600 bg-purple-50 px-2 py-1 rounded-full">
                  <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                  생성 중...
                </span>
              )}
              {statusMessage && (
                <span className="text-sm text-purple-600">{statusMessage}</span>
              )}
            </div>
            {!isStreaming && streamingText && (
              <button
                onClick={() => { setStreamingText(''); setStreamingSections(initialSections); }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                닫기
              </button>
            )}
          </div>

          {/* 시황 요약 + 시장 심리 */}
          {(streamingSections.summary || streamingSections.sentiment) && (
            <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-purple-900">AI 시황 요약</h3>
                </div>
                {streamingSections.sentiment && (
                  <span className="px-3 py-1 rounded-full text-sm font-medium border bg-purple-100 text-purple-700 border-purple-200">
                    {streamingSections.sentiment.split('\n')[0]}
                  </span>
                )}
              </div>
              <p className="text-gray-700 leading-relaxed">
                {streamingSections.summary}
                {isStreaming && currentSection.includes('시황 요약') && <span className="animate-pulse">|</span>}
              </p>
            </div>
          )}

          {/* 기술적 지표 분석 */}
          {streamingSections.technicalAnalysis && (
            <div className="card bg-gray-50">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold">기술적 지표 분석</h3>
              </div>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {streamingSections.technicalAnalysis}
                {isStreaming && currentSection.includes('기술적') && <span className="animate-pulse">|</span>}
              </p>
            </div>
          )}

          {/* 원자재 및 비트코인 */}
          {streamingSections.commoditiesAnalysis && (
            <div className="card bg-amber-50 border-amber-100">
              <div className="flex items-center gap-2 mb-3">
                <Coins className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">원자재 및 비트코인</h3>
              </div>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {streamingSections.commoditiesAnalysis}
                {isStreaming && currentSection.includes('원자재') && <span className="animate-pulse">|</span>}
              </p>
            </div>
          )}

          {/* 지수별 분석 */}
          {(streamingSections.kospiAnalysis || streamingSections.kosdaqAnalysis || streamingSections.nasdaqAnalysis) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {streamingSections.kospiAnalysis && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="w-5 h-5 text-red-500" />
                    <h4 className="font-semibold">코스피 분석</h4>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {streamingSections.kospiAnalysis}
                    {isStreaming && currentSection.includes('코스피') && <span className="animate-pulse">|</span>}
                  </p>
                </div>
              )}
              {streamingSections.kosdaqAnalysis && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingDown className="w-5 h-5 text-blue-500" />
                    <h4 className="font-semibold">코스닥 분석</h4>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {streamingSections.kosdaqAnalysis}
                    {isStreaming && currentSection.includes('코스닥') && <span className="animate-pulse">|</span>}
                  </p>
                </div>
              )}
              {streamingSections.nasdaqAnalysis && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-5 h-5 text-green-500" />
                    <h4 className="font-semibold">나스닥 분석</h4>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {streamingSections.nasdaqAnalysis}
                    {isStreaming && currentSection.includes('나스닥') && <span className="animate-pulse">|</span>}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* 유망 테마 */}
          {(streamingSections.theme1.name || streamingSections.theme2.name || streamingSections.theme3.name) && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Flame className="w-5 h-5 text-orange-500" />
                <h3 className="font-semibold">유망 테마 TOP 3</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[streamingSections.theme1, streamingSections.theme2, streamingSections.theme3].map((theme, index) =>
                  theme?.name ? (
                    <div key={index} className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-4 border border-orange-100">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </span>
                        <h4 className="font-semibold text-gray-800">{theme.name}</h4>
                      </div>
                      <p className="text-sm text-gray-600 whitespace-pre-line">
                        {theme?.content ?? ''}
                        {isStreaming && currentSection.includes(`${index + 1}.`) && <span className="animate-pulse">|</span>}
                      </p>
                    </div>
                  ) : null
                )}
              </div>
            </div>
          )}

          {/* 보유 종목 전망 및 전략 - 종목별 카드 */}
          {streamingSections.holdingsStrategy && (() => {
            const holdingCards = parseHoldingsStrategy(streamingSections.holdingsStrategy)
            return (
            <div className="card border-l-4 border-l-indigo-400">
              <div className="flex items-center gap-2 mb-3">
                <ClipboardList className="w-5 h-5 text-indigo-600" />
                <h4 className="font-semibold text-indigo-700">보유 종목 전망 및 전략</h4>
              </div>
              {holdingCards && Array.isArray(holdingCards) ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(holdingCards as HoldingCard[]).map((card, idx) => (
                    <div key={idx} className="bg-white rounded-xl border border-indigo-100 p-4 shadow-sm hover:shadow-md transition-shadow">
                      <div className="font-semibold text-indigo-800 mb-3 pb-2 border-b border-indigo-100">{card.name}</div>
                      {card.outlook && <p className="text-sm text-gray-600 mb-2"><span className="text-indigo-600 font-medium">전망</span> {card.outlook}</p>}
                      {card.strategy && <p className="text-sm text-gray-700"><span className="text-green-600 font-medium">전략</span> {card.strategy}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600 whitespace-pre-line">
                  {streamingSections.holdingsStrategy}
                  {isStreaming && currentSection.includes('보유 종목') && <span className="animate-pulse">|</span>}
                </p>
              )}
            </div>
            )
          })()}

          {/* 리스크 요인 & 투자 전략 */}
          {(streamingSections.riskFactors || streamingSections.recommendation) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {streamingSections.riskFactors && (
                <div className="card border-l-4 border-l-red-400">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <h4 className="font-semibold text-red-700">리스크 요인</h4>
                  </div>
                  <p className="text-sm text-gray-600 whitespace-pre-line">
                    {streamingSections.riskFactors}
                    {isStreaming && currentSection.includes('리스크') && <span className="animate-pulse">|</span>}
                  </p>
                </div>
              )}
              {streamingSections.recommendation && (
                <div className="card border-l-4 border-l-green-400">
                  <div className="flex items-center gap-2 mb-3">
                    <Target className="w-5 h-5 text-green-500" />
                    <h4 className="font-semibold text-green-700">투자 전략 제안</h4>
                  </div>
                  <p className="text-sm text-gray-600 whitespace-pre-line">
                    {streamingSections.recommendation}
                    {isStreaming && currentSection.includes('투자 전략') && <span className="animate-pulse">|</span>}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* AI 분석 결과 (구조화) */}
      {analysis && (
        <div className="space-y-6">
          {analysis.isMock && (
            <div className="card border-amber-200 bg-amber-50 text-amber-800 text-sm">
              <strong>기본 안내만 표시 중입니다.</strong> OpenAI API 호출에 실패해 임시 문구가 나왔을 수 있습니다. 백엔드의 OPENAI_API_KEY 설정과 네트워크를 확인해 주세요.
            </div>
          )}
          {/* 시황 요약 + 시장 심리 */}
          <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-purple-900">AI 시황 요약</h3>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${sentimentColors[analysis.marketSentiment] || sentimentColors['중립']}`}>
                시장 심리: {analysis.marketSentiment}
              </span>
            </div>
            <p className="text-gray-700 leading-relaxed">{analysis.summary}</p>
            <p className="text-xs text-gray-400 mt-3">생성 시간: {analysis.generatedAt}</p>
          </div>

          {/* 뉴스 분석 */}
          {analysis.newsAnalysis && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <Newspaper className="w-5 h-5 text-indigo-600" />
                <h3 className="font-semibold">뉴스 심층 분석</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">{analysis.newsAnalysis}</p>
            </div>
          )}

          {/* 기술적 지표 분석 */}
          {analysis.technicalSummary && (
            <div className="card bg-gray-50">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold">기술적 지표 분석</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                {/* RSI */}
                <div className="bg-white rounded-lg p-4 border">
                  <div className="text-sm text-gray-500 mb-1">평균 RSI</div>
                  <div className={`text-2xl font-bold ${getRsiColor(analysis.technicalSummary.avgRsi)}`}>
                    {analysis.technicalSummary.avgRsi?.toFixed(1) || '-'}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {analysis.technicalSummary.avgRsi >= 70 ? '과매수' : 
                     analysis.technicalSummary.avgRsi <= 30 ? '과매도' : '중립'}
                  </div>
                </div>
                
                {/* 종합 판단 */}
                <div className="bg-white rounded-lg p-4 border md:col-span-3">
                  <div className="text-sm text-gray-500 mb-1">종합 판단</div>
                  <div className="text-lg font-semibold text-gray-800">
                    {analysis.technicalSummary.overall}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-3 border">
                  <div className="text-sm font-medium text-gray-700 mb-1">RSI 분석</div>
                  <p className="text-sm text-gray-600">{analysis.technicalSummary.rsiStatus}</p>
                </div>
                <div className="bg-white rounded-lg p-3 border">
                  <div className="text-sm font-medium text-gray-700 mb-1">볼린저밴드</div>
                  <p className="text-sm text-gray-600">{analysis.technicalSummary.bollingerStatus}</p>
                </div>
                <div className="bg-white rounded-lg p-3 border">
                  <div className="text-sm font-medium text-gray-700 mb-1">이동평균선</div>
                  <p className="text-sm text-gray-600">{analysis.technicalSummary.maStatus}</p>
                </div>
              </div>

              {/* 과매도/과매수 종목 */}
              {(analysis.technicalSummary.oversoldStocks?.length > 0 || analysis.technicalSummary.overboughtStocks?.length > 0) && (
                <div className="mt-4 flex flex-wrap gap-4">
                  {analysis.technicalSummary.oversoldStocks?.length > 0 && (
                    <div className="flex items-center gap-2">
                      <ArrowDownCircle className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-gray-600">과매도: </span>
                      <span className="text-sm font-medium text-blue-600">
                        {analysis.technicalSummary.oversoldStocks.join(', ')}
                      </span>
                    </div>
                  )}
                  {analysis.technicalSummary.overboughtStocks?.length > 0 && (
                    <div className="flex items-center gap-2">
                      <ArrowUpCircle className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-gray-600">과매수: </span>
                      <span className="text-sm font-medium text-red-600">
                        {analysis.technicalSummary.overboughtStocks.join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 원자재 및 비트코인 */}
          {analysis.commoditiesAnalysis && (
            <div className="card bg-amber-50 border-amber-100">
              <div className="flex items-center gap-2 mb-3">
                <Coins className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">원자재 및 비트코인</h3>
              </div>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">{analysis.commoditiesAnalysis}</p>
            </div>
          )}

          {/* 보유 종목 전망 및 전략 - 종목별 카드 */}
          <div className="card border-l-4 border-l-indigo-400">
            <div className="flex items-center gap-2 mb-3">
              <ClipboardList className="w-5 h-5 text-indigo-600" />
              <h4 className="font-semibold text-indigo-700">보유 종목 전망 및 전략</h4>
            </div>
            {(() => {
              const holdingCards = analysis.holdingsStrategy ? parseHoldingsStrategy(analysis.holdingsStrategy) : null
              return holdingCards && Array.isArray(holdingCards) ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(holdingCards as HoldingCard[]).map((card, idx) => (
                  <div key={idx} className="bg-white rounded-xl border border-indigo-100 p-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="font-semibold text-indigo-800 mb-3 pb-2 border-b border-indigo-100">{card.name}</div>
                    {card.outlook && <p className="text-sm text-gray-600 mb-2"><span className="text-indigo-600 font-medium">전망</span> {card.outlook}</p>}
                    {card.strategy && <p className="text-sm text-gray-700"><span className="text-green-600 font-medium">전략</span> {card.strategy}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-600 whitespace-pre-line">
                {analysis.holdingsStrategy || '보유 종목이 없거나 해당 분석 결과가 비어 있습니다.'}
              </p>
            )
            })()}
          </div>

          {/* 지수별 분석 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-5 h-5 text-red-500" />
                <h4 className="font-semibold">코스피 분석</h4>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{analysis.kospiAnalysis}</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="w-5 h-5 text-blue-500" />
                <h4 className="font-semibold">코스닥 분석</h4>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{analysis.kosdaqAnalysis}</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-5 h-5 text-green-500" />
                <h4 className="font-semibold">나스닥 분석</h4>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{analysis.nasdaqAnalysis}</p>
            </div>
          </div>

          {/* 유망 테마 */}
          {Array.isArray(analysis.hotThemes) && analysis.hotThemes.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Flame className="w-5 h-5 text-orange-500" />
                <h3 className="font-semibold">유망 테마 TOP 3</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(Array.isArray(analysis.hotThemes) ? analysis.hotThemes : []).map((theme, index) => (
                    <div key={index} className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-4 border border-orange-100">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </span>
                      <h4 className="font-semibold text-gray-800">{theme?.name ?? ''}</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{theme?.reason ?? ''}</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">코스피 대장주</span>
                        <span className="font-medium text-red-600">{theme?.kospiLeader ?? '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">코스닥 대장주</span>
                        <span className="font-medium text-blue-600">{theme?.kosdaqLeader ?? '-'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 리스크 요인 & 액션 아이템 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 리스크 요인 */}
            {Array.isArray(analysis.riskFactors) && analysis.riskFactors.length > 0 && (
              <div className="card border-l-4 border-l-red-400">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <h4 className="font-semibold text-red-700">리스크 요인</h4>
                </div>
                <ul className="space-y-2">
                  {(Array.isArray(analysis.riskFactors) ? analysis.riskFactors : []).map((risk, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-red-400 mt-1">•</span>
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 액션 아이템 */}
            {Array.isArray(analysis.actionItems) && analysis.actionItems.length > 0 && (
              <div className="card border-l-4 border-l-green-400">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <h4 className="font-semibold text-green-700">액션 아이템</h4>
                </div>
                <ul className="space-y-2">
                  {(Array.isArray(analysis.actionItems) ? analysis.actionItems : []).map((action, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-green-400 mt-1">•</span>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* 투자 전략 제안 */}
          <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-primary-700">투자 전략 제안</h4>
            </div>
            <p className="text-gray-700 leading-relaxed">{analysis.recommendation}</p>
          </div>
        </div>
      )}

      {/* 뉴스 섹션 */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold">실시간 증시 뉴스</h3>
          </div>
          <button
            onClick={fetchNews}
            disabled={loading}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
        </div>
        <div className="divide-y divide-gray-100">
          {(Array.isArray(news) ? news : []).map((item, index) => (
            <a
              key={index}
              href={item?.url ?? '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="block py-3 hover:bg-gray-50 -mx-6 px-6 transition-colors"
            >
              <p className="text-gray-900 font-medium">{item?.title ?? ''}</p>
              <div className="flex gap-2 mt-1 text-sm text-gray-500">
                <span>{item?.source ?? '-'}</span>
                <span>·</span>
                <span>{item?.time ?? '-'}</span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
