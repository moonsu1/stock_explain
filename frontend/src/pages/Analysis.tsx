import { useEffect, useState, useRef } from 'react'
import { 
  RefreshCw, Newspaper, TrendingUp, TrendingDown, Sparkles, 
  Activity, Target, AlertTriangle, CheckCircle, Flame,
  BarChart3, ArrowUpCircle, ArrowDownCircle, Zap
} from 'lucide-react'
import axios from 'axios'

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

// 스트리밍 섹션 타입
interface StreamingSections {
  summary: string
  sentiment: string
  kospiAnalysis: string
  kosdaqAnalysis: string
  nasdaqAnalysis: string
  technicalAnalysis: string
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
  theme1: { name: '', content: '' },
  theme2: { name: '', content: '' },
  theme3: { name: '', content: '' },
  riskFactors: '',
  recommendation: ''
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
      setNews(response.data)
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
    try {
      const response = await axios.post('/api/analysis/generate')
      setAnalysis(response.data)
    } catch (error) {
      console.error('분석 생성 실패:', error)
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
    setAnalysis(null)
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      console.log('[Stream] Fetching streaming API')
      const response = await fetch(`${apiUrl}/api/analysis/generate/stream`)
      console.log('[Stream] Response status:', response.status, response.ok)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
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
              setStatusMessage(data.replace('[ERROR] ', ''))
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
      setStatusMessage('분석 중 오류가 발생했습니다.')
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
                {[streamingSections.theme1, streamingSections.theme2, streamingSections.theme3].map((theme, index) => (
                  theme.name && (
                    <div key={index} className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-4 border border-orange-100">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </span>
                        <h4 className="font-semibold text-gray-800">{theme.name}</h4>
                      </div>
                      <p className="text-sm text-gray-600 whitespace-pre-line">
                        {theme.content}
                        {isStreaming && currentSection.includes(`${index + 1}.`) && <span className="animate-pulse">|</span>}
                      </p>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

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
          {analysis.hotThemes && analysis.hotThemes.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Flame className="w-5 h-5 text-orange-500" />
                <h3 className="font-semibold">유망 테마 TOP 3</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {analysis.hotThemes.map((theme, index) => (
                  <div key={index} className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-4 border border-orange-100">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </span>
                      <h4 className="font-semibold text-gray-800">{theme.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{theme.reason}</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">코스피 대장주</span>
                        <span className="font-medium text-red-600">{theme.kospiLeader}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">코스닥 대장주</span>
                        <span className="font-medium text-blue-600">{theme.kosdaqLeader}</span>
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
            {analysis.riskFactors && analysis.riskFactors.length > 0 && (
              <div className="card border-l-4 border-l-red-400">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <h4 className="font-semibold text-red-700">리스크 요인</h4>
                </div>
                <ul className="space-y-2">
                  {analysis.riskFactors.map((risk, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-red-400 mt-1">•</span>
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 액션 아이템 */}
            {analysis.actionItems && analysis.actionItems.length > 0 && (
              <div className="card border-l-4 border-l-green-400">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <h4 className="font-semibold text-green-700">액션 아이템</h4>
                </div>
                <ul className="space-y-2">
                  {analysis.actionItems.map((action, index) => (
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
          {news.map((item, index) => (
            <a
              key={index}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block py-3 hover:bg-gray-50 -mx-6 px-6 transition-colors"
            >
              <p className="text-gray-900 font-medium">{item.title}</p>
              <div className="flex gap-2 mt-1 text-sm text-gray-500">
                <span>{item.source}</span>
                <span>·</span>
                <span>{item.time}</span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
