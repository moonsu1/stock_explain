# -*- coding: utf-8 -*-
"""
시황 분석 모듈 (Professional Version)

GPT를 활용하여 기술적 지표, 뉴스 기반 시황 분석, 유망 테마/대장주 추천을 제공합니다.
"""
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json

from dotenv import load_dotenv
load_dotenv(override=True)

# OpenAI 임포트
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 스트리밍 타입
from typing import Generator

try:
    from .news import news_crawler, NewsItem
    from .crawler import get_all_indices, get_stock_price, IndexData
    from .technical import (
        analyze_multiple_stocks, 
        format_technical_for_prompt,
        get_market_technical_summary,
        TechnicalIndicators
    )
except ImportError:
    from news import news_crawler, NewsItem
    from crawler import get_all_indices, get_stock_price, IndexData
    from technical import (
        analyze_multiple_stocks, 
        format_technical_for_prompt,
        get_market_technical_summary,
        TechnicalIndicators
    )


@dataclass
class MarketIndex:
    """시장 지수"""
    name: str
    value: float
    change: float
    change_percent: float


@dataclass
class HotTheme:
    """유망 테마"""
    name: str
    reason: str
    kospi_leader: str
    kosdaq_leader: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "reason": self.reason,
            "kospiLeader": self.kospi_leader,
            "kosdaqLeader": self.kosdaq_leader
        }


@dataclass
class TechnicalSummary:
    """기술적 지표 요약"""
    overall: str
    avg_rsi: float
    rsi_status: str
    bollinger_status: str
    ma_status: str
    oversold_stocks: List[str] = field(default_factory=list)
    overbought_stocks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "overall": self.overall,
            "avgRsi": self.avg_rsi,
            "rsiStatus": self.rsi_status,
            "bollingerStatus": self.bollinger_status,
            "maStatus": self.ma_status,
            "oversoldStocks": self.oversold_stocks,
            "overboughtStocks": self.overbought_stocks
        }


@dataclass
class MarketAnalysis:
    """시황 분석 결과 (확장 버전)"""
    # 기본 분석
    summary: str
    news_analysis: str
    kospi_analysis: str
    kosdaq_analysis: str
    nasdaq_analysis: str
    
    # 기술적 지표
    technical_summary: TechnicalSummary
    
    # 투자 전략
    market_sentiment: str  # 공포/중립/탐욕
    hot_themes: List[HotTheme]
    risk_factors: List[str]
    action_items: List[str]
    recommendation: str
    
    generated_at: str
    
    def to_dict(self) -> Dict:
        return {
            "summary": self.summary,
            "newsAnalysis": self.news_analysis,
            "kospiAnalysis": self.kospi_analysis,
            "kosdaqAnalysis": self.kosdaq_analysis,
            "nasdaqAnalysis": self.nasdaq_analysis,
            "technicalSummary": self.technical_summary.to_dict(),
            "marketSentiment": self.market_sentiment,
            "hotThemes": [t.to_dict() for t in self.hot_themes],
            "riskFactors": self.risk_factors,
            "actionItems": self.action_items,
            "recommendation": self.recommendation,
            "generatedAt": self.generated_at
        }


class MarketAnalyzer:
    """시황 분석기 (Professional Version)"""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        
        print(f"[Debug] API Key: {api_key[:30] if api_key else 'None'}...")
        print(f"[Debug] Model: {self.model}, Max Tokens: {self.max_tokens}")
        
        if OPENAI_AVAILABLE and api_key and api_key.startswith("sk-"):
            try:
                self.client = OpenAI(api_key=api_key)
                print(f"[OK] OpenAI API connected (client={self.client is not None})")
            except Exception as e:
                print(f"[Warning] OpenAI init failed: {e}")
                self.client = None
        else:
            if not OPENAI_AVAILABLE:
                print("[Warning] openai library not installed")
            elif not api_key:
                print("[Warning] OPENAI_API_KEY not set")
    
    def get_market_indices(self) -> List[MarketIndex]:
        """주요 지수 조회"""
        indices = []
        crawled = get_all_indices()
        
        for idx in crawled:
            indices.append(MarketIndex(
                name=idx.name,
                value=idx.value,
                change=idx.change,
                change_percent=idx.change_percent
            ))
        
        return indices
    
    def get_news(self, limit: int = 10) -> List[Dict]:
        """뉴스 목록 조회"""
        news = news_crawler.get_market_headlines()
        return [n.to_dict() for n in news[:limit]]
    
    def get_technical_indicators(self, codes: List[str] = None) -> List[TechnicalIndicators]:
        """기술적 지표 조회"""
        return analyze_multiple_stocks(codes)
    
    def generate_analysis(self, user_holdings: List[str] = None) -> MarketAnalysis:
        """AI 시황 분석 생성"""
        print(f"[Debug] generate_analysis called, client={self.client is not None}")
        
        # 데이터 수집
        print("[Info] Collecting market data...")
        indices = self.get_market_indices()
        news = news_crawler.get_market_headlines()
        
        print("[Info] Calculating technical indicators...")
        technical_indicators = self.get_technical_indicators()
        tech_summary = get_market_technical_summary(technical_indicators)
        
        # GPT 클라이언트가 없으면 모의 분석 반환
        if not self.client:
            print("[Info] Using mock analysis (no OpenAI client)")
            return self._generate_mock_analysis(indices, news, technical_indicators, user_holdings)
        
        try:
            # 프롬프트 구성
            prompt = self._build_analysis_prompt(indices, news, technical_indicators, user_holdings)
            
            print("[Info] Calling OpenAI API...")
            print(f"[Info] Using model: {self.model}, max_tokens: {self.max_tokens}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # 낮은 temperature로 일관성 높임
            )
            
            content = response.choices[0].message.content
            print(f"[Debug] Raw response length: {len(content) if content else 0}")
            
            if not content:
                print("[Error] Empty response from GPT")
                return self._generate_mock_analysis(indices, news, technical_indicators, user_holdings)
            
            content = content.strip()
            
            # JSON 추출
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis_data = json.loads(content)
            print("[OK] GPT analysis complete")
            
            return self._parse_analysis_response(analysis_data, tech_summary)
            
        except json.JSONDecodeError as e:
            print(f"[Error] JSON parse failed: {e}")
            return self._generate_mock_analysis(indices, news, technical_indicators, user_holdings)
        except Exception as e:
            print(f"[Error] GPT analysis failed: {e}")
            return self._generate_mock_analysis(indices, news, technical_indicators, user_holdings)
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 10년 이상 경력의 증권사 리서치센터 수석 애널리스트입니다.

역할:
- 개인 투자자에게 전문적인 시황 분석과 투자 전략을 제공
- 기술적 지표와 뉴스를 종합하여 시장 상황을 심층 분석
- 유망 테마와 대장주를 발굴하여 투자 아이디어 제공

중요 - 일관된 판단 기준:
1. 시장 심리 판단 기준 (반드시 이 기준 적용):
   - RSI 30 이하 + 지수 -2% 이상 하락 = "공포"
   - RSI 30-40 + 지수 하락 = "불안"  
   - RSI 40-60 = "중립"
   - RSI 60-70 + 지수 상승 = "낙관"
   - RSI 70 이상 + 지수 +2% 이상 상승 = "탐욕"

2. 유망 테마 선정 기준:
   - 최근 뉴스에서 자주 언급되는 섹터
   - 정부 정책 수혜 섹터
   - 글로벌 트렌드 관련 섹터
   - 반드시 뉴스 근거를 제시

3. 투자 전략 판단 기준:
   - RSI 30 이하: 분할 매수 구간
   - RSI 70 이상: 차익실현 고려
   - 이동평균선 정배열: 상승 추세
   - 이동평균선 역배열: 하락 추세

응답 스타일:
- 데이터와 수치에 기반한 객관적 분석
- 구체적인 근거와 함께 제시
- 반드시 순수 JSON 형식으로만 응답 (마크다운 코드블록 없이)"""
    
    def _build_analysis_prompt(
        self, 
        indices: List[MarketIndex], 
        news: List[NewsItem],
        technical_indicators: List[TechnicalIndicators],
        user_holdings: List[str] = None
    ) -> str:
        """분석 프롬프트 생성"""
        
        # 지수 정보
        indices_text = "\n".join([
            f"- {idx.name}: {idx.value:,.2f} ({'+' if idx.change >= 0 else ''}{idx.change:,.2f}, {idx.change_percent:+.2f}%)"
            for idx in indices
        ])
        
        # 뉴스 헤드라인
        news_text = "\n".join([
            f"- [{n.source}] {n.title}"
            for n in news[:15]
        ])
        
        # 기술적 지표
        tech_text = format_technical_for_prompt(technical_indicators)
        
        # 보유 종목 정보
        holdings_text = ""
        if user_holdings:
            holdings_text = f"\n\n## 사용자 보유 종목\n{', '.join(user_holdings)}"
        
        prompt = f"""다음 시장 데이터를 분석하여 전문 애널리스트 수준의 시황 리포트를 작성해주세요.

## 주요 지수 (실시간)
{indices_text}

## 주요 뉴스 헤드라인
{news_text}

{tech_text}
{holdings_text}

위 데이터를 바탕으로 다음 JSON 형식으로 분석해주세요:

{{
    "summary": "오늘 시장 상황 종합 요약 (3-4문장, 핵심 이슈와 시장 분위기 포함)",
    
    "news_analysis": "주요 뉴스 심층 분석 (어떤 뉴스가 시장에 영향을 미쳤는지, 향후 영향 전망 포함)",
    
    "kospi_analysis": "코스피 상세 분석 (등락 원인, 외국인/기관 수급 추정, 주요 섹터 동향)",
    
    "kosdaq_analysis": "코스닥 상세 분석 (등락 원인, 테마주 동향, 중소형주 흐름)",
    
    "nasdaq_analysis": "나스닥 분석 및 국내 영향 (기술주 동향, 국내 시장 영향도)",
    
    "technical_analysis": {{
        "overall": "기술적 지표 종합 판단 (과매수/과매도/중립 등)",
        "rsi_comment": "RSI 기반 분석 코멘트",
        "bb_comment": "볼린저밴드 기반 분석 코멘트",
        "ma_comment": "이동평균선 기반 분석 코멘트"
    }},
    
    "market_sentiment": "현재 시장 심리 (공포/불안/중립/낙관/탐욕 중 하나)",
    
    "hot_themes": [
        {{
            "name": "테마명",
            "reason": "해당 테마가 유망한 이유 (구체적 뉴스/이벤트 기반)",
            "kospi_leader": "코스피 대장주 (종목명)",
            "kosdaq_leader": "코스닥 대장주 (종목명)"
        }}
    ],
    
    "risk_factors": ["리스크 요인 1", "리스크 요인 2", "리스크 요인 3"],
    
    "action_items": [
        "구체적인 투자 액션 1 (예: 특정 구간에서 분할 매수)",
        "구체적인 투자 액션 2",
        "구체적인 투자 액션 3"
    ],
    
    "recommendation": "종합 투자 전략 (현재 시장 상황에서 어떻게 대응해야 하는지 2-3문장)"
}}

유망 테마는 반드시 3개를 제시해주세요. 뉴스와 시장 상황을 고려하여 현실적인 테마와 대장주를 추천해주세요."""

        return prompt
    
    def generate_analysis_stream(self, user_holdings: List[str] = None) -> Generator[str, None, None]:
        """AI 시황 분석 스트리밍 생성"""
        print(f"[Debug] generate_analysis_stream called, client={self.client is not None}")
        
        # 데이터 수집 단계 알림
        yield "data: [STATUS] 시장 데이터 수집 중...\n\n"
        
        print("[Info] Collecting market data...")
        indices = self.get_market_indices()
        news = news_crawler.get_market_headlines()
        
        yield "data: [STATUS] 기술적 지표 분석 중...\n\n"
        
        print("[Info] Calculating technical indicators...")
        technical_indicators = self.get_technical_indicators()
        tech_summary = get_market_technical_summary(technical_indicators)
        
        # GPT 클라이언트가 없으면 에러
        if not self.client:
            yield "data: [ERROR] OpenAI API가 설정되지 않았습니다.\n\n"
            yield "data: [DONE]\n\n"
            return
        
        try:
            yield "data: [STATUS] AI 분석 시작...\n\n"
            
            # 스트리밍용 프롬프트 (텍스트 형식)
            prompt = self._build_streaming_prompt(indices, news, technical_indicators, user_holdings)
            
            print("[Info] Calling OpenAI API with streaming...")
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_streaming_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,  # 낮은 temperature로 일관성 높임
                stream=True
            )
            
            # 스트리밍 응답 전송
            full_content = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    # SSE 형식으로 전송 (줄바꿈은 특별 처리)
                    escaped = content.replace("\n", "\\n")
                    yield f"data: {escaped}\n\n"
            
            print(f"[OK] Streaming complete, total length: {len(full_content)}")
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"[Error] Streaming failed: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    
    def _get_streaming_system_prompt(self) -> str:
        """스트리밍용 시스템 프롬프트"""
        return """당신은 10년 이상 경력의 증권사 리서치센터 수석 애널리스트입니다.

역할:
- 개인 투자자에게 전문적인 시황 분석과 투자 전략을 제공
- 기술적 지표와 뉴스를 종합하여 시장 상황을 심층 분석
- 유망 테마와 대장주를 발굴하여 투자 아이디어 제공

중요 - 일관된 판단 기준 (반드시 이 기준으로 판단):
1. 시장 심리:
   - RSI 30 이하 + 지수 -2% 이상 하락 = "공포"
   - RSI 30-40 + 지수 하락 = "불안"  
   - RSI 40-60 = "중립"
   - RSI 60-70 + 지수 상승 = "낙관"
   - RSI 70 이상 + 지수 +2% 이상 상승 = "탐욕"

2. 투자 전략:
   - RSI 30 이하: 분할 매수 구간
   - RSI 70 이상: 차익실현 고려
   - 이동평균선 정배열: 상승 추세
   - 이동평균선 역배열: 하락 추세

응답 스타일:
- 마크다운 형식으로 깔끔하게 정리
- 이모지 사용하지 말것
- 데이터와 수치에 기반한 객관적 분석
- 뉴스 근거와 함께 제시"""
    
    def _build_streaming_prompt(
        self, 
        indices: List[MarketIndex], 
        news: List[NewsItem],
        technical_indicators: List[TechnicalIndicators],
        user_holdings: List[str] = None
    ) -> str:
        """스트리밍용 프롬프트 생성"""
        
        # 지수 정보
        indices_text = "\n".join([
            f"- {idx.name}: {idx.value:,.2f} ({'+' if idx.change >= 0 else ''}{idx.change:,.2f}, {idx.change_percent:+.2f}%)"
            for idx in indices
        ])
        
        # 뉴스 헤드라인
        news_text = "\n".join([
            f"- [{n.source}] {n.title}"
            for n in news[:10]
        ])
        
        # 기술적 지표
        tech_text = format_technical_for_prompt(technical_indicators)
        
        # 보유 종목 정보
        holdings_text = ""
        if user_holdings:
            holdings_text = f"\n\n## 사용자 보유 종목\n{', '.join(user_holdings)}"
        
        prompt = f"""다음 시장 데이터를 분석하여 전문 애널리스트 수준의 시황 리포트를 작성해주세요.

## 데이터 출처
- 지수 데이터: 네이버 금융 실시간 시세
- 뉴스: 네이버 금융 뉴스 섹션
- 기술적 지표: 종목별 계산 값

## 주요 지수 (실시간)
{indices_text}

## 주요 뉴스 헤드라인
{news_text}

{tech_text}
{holdings_text}

중요: 위에서 제공한 데이터만을 근거로 분석하세요. 주관적 추측보다 수치 기반 판단을 우선하세요.

다음 형식으로 분석해주세요:

## 오늘의 시황 요약
(3-4문장으로 핵심 이슈와 시장 분위기 요약 - 뉴스 헤드라인 근거 인용)

## 시장 심리
(공포/불안/중립/낙관/탐욕 중 하나 - RSI와 지수 등락률 기준으로 판단하고 그 근거 명시)

## 지수별 분석

### 코스피
(등락 원인, 외국인/기관 수급 추정, 주요 섹터 동향)

### 코스닥  
(등락 원인, 테마주 동향, 중소형주 흐름)

### 나스닥
(기술주 동향, 국내 시장 영향도)

## 기술적 지표 해석
(RSI, 볼린저밴드, 이동평균선 분석 및 시사점)

## 유망 테마 TOP 3

### 1. [테마명]
- 유망 이유: (구체적 이유)
- 코스피 대장주: [종목명]
- 코스닥 대장주: [종목명]

### 2. [테마명]
- 유망 이유: (구체적 이유)
- 코스피 대장주: [종목명]
- 코스닥 대장주: [종목명]

### 3. [테마명]
- 유망 이유: (구체적 이유)
- 코스피 대장주: [종목명]
- 코스닥 대장주: [종목명]

## 리스크 요인
- (리스크 1)
- (리스크 2)
- (리스크 3)

## 투자 전략 제안
(현재 시장 상황에서 어떻게 대응해야 하는지 구체적 액션 포함)"""

        return prompt

    def _parse_analysis_response(self, data: Dict, tech_summary: Dict) -> MarketAnalysis:
        """GPT 응답 파싱"""
        
        # 기술적 분석 파싱
        tech_data = data.get("technical_analysis", {})
        technical_summary = TechnicalSummary(
            overall=tech_data.get("overall", tech_summary.get("overall", "분석 중")),
            avg_rsi=tech_summary.get("avg_rsi", 50),
            rsi_status=tech_data.get("rsi_comment", ""),
            bollinger_status=tech_data.get("bb_comment", ""),
            ma_status=tech_data.get("ma_comment", ""),
            oversold_stocks=tech_summary.get("oversold_stocks", []),
            overbought_stocks=tech_summary.get("overbought_stocks", [])
        )
        
        # 유망 테마 파싱
        hot_themes = []
        for theme in data.get("hot_themes", []):
            hot_themes.append(HotTheme(
                name=theme.get("name", ""),
                reason=theme.get("reason", ""),
                kospi_leader=theme.get("kospi_leader", ""),
                kosdaq_leader=theme.get("kosdaq_leader", "")
            ))
        
        return MarketAnalysis(
            summary=data.get("summary", ""),
            news_analysis=data.get("news_analysis", ""),
            kospi_analysis=data.get("kospi_analysis", ""),
            kosdaq_analysis=data.get("kosdaq_analysis", ""),
            nasdaq_analysis=data.get("nasdaq_analysis", ""),
            technical_summary=technical_summary,
            market_sentiment=data.get("market_sentiment", "중립"),
            hot_themes=hot_themes,
            risk_factors=data.get("risk_factors", []),
            action_items=data.get("action_items", []),
            recommendation=data.get("recommendation", ""),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _generate_mock_analysis(
        self,
        indices: List[MarketIndex],
        news: List[NewsItem],
        technical_indicators: List[TechnicalIndicators],
        user_holdings: List[str] = None
    ) -> MarketAnalysis:
        """모의 분석 생성"""
        
        # 지수 데이터
        kospi = next((i for i in indices if i.name == "코스피"), None)
        kosdaq = next((i for i in indices if i.name == "코스닥"), None)
        nasdaq = next((i for i in indices if i.name == "나스닥"), None)
        
        kospi_status = "상승" if kospi and kospi.change >= 0 else "하락"
        kosdaq_status = "상승" if kosdaq and kosdaq.change >= 0 else "하락"
        
        # 기술적 지표 요약
        tech_summary = get_market_technical_summary(technical_indicators)
        
        technical_summary = TechnicalSummary(
            overall=tech_summary.get("overall", "분석 중"),
            avg_rsi=tech_summary.get("avg_rsi", 50),
            rsi_status=f"평균 RSI {tech_summary.get('avg_rsi', 50):.1f}",
            bollinger_status="밴드 내 움직임",
            ma_status="혼조세",
            oversold_stocks=tech_summary.get("oversold_stocks", []),
            overbought_stocks=tech_summary.get("overbought_stocks", [])
        )
        
        # 요약
        summary = f"오늘 코스피는 {kospi.value:,.2f}pt로 {kospi_status}({kospi.change_percent:+.2f}%), "
        summary += f"코스닥은 {kosdaq.value:,.2f}pt로 {kosdaq_status}({kosdaq.change_percent:+.2f}%) 마감했습니다. "
        summary += f"기술적으로는 {tech_summary.get('overall', '혼조세')} 상황입니다."
        
        # 뉴스 분석
        news_titles = [n.title for n in news[:5]]
        news_analysis = f"주요 뉴스: {', '.join(news_titles[:3])}. 시장에 영향을 미치고 있습니다."
        
        # 기본 테마
        hot_themes = [
            HotTheme("2차전지", "전기차 시장 확대로 수혜 예상", "LG에너지솔루션", "에코프로비엠"),
            HotTheme("반도체", "AI 수요 증가로 메모리 반도체 수혜", "삼성전자", "리노공업"),
            HotTheme("바이오", "신약 개발 모멘텀 지속", "삼성바이오로직스", "셀트리온헬스케어")
        ]
        
        return MarketAnalysis(
            summary=summary,
            news_analysis=news_analysis,
            kospi_analysis=f"코스피는 {kospi.value:,.2f}pt로 전일 대비 {kospi.change:+,.2f}pt({kospi.change_percent:+.2f}%) {kospi_status}했습니다.",
            kosdaq_analysis=f"코스닥은 {kosdaq.value:,.2f}pt로 전일 대비 {kosdaq.change:+,.2f}pt({kosdaq.change_percent:+.2f}%) {kosdaq_status}했습니다.",
            nasdaq_analysis=f"나스닥은 {nasdaq.value:,.2f}pt로 {nasdaq.change_percent:+.2f}% 변동했습니다.",
            technical_summary=technical_summary,
            market_sentiment="중립",
            hot_themes=hot_themes,
            risk_factors=["글로벌 금리 인상", "지정학적 리스크", "경기 둔화 우려"],
            action_items=[
                "시장 변동성 확대에 대비하여 현금 비중 유지",
                "과매도 구간 진입 시 분할 매수 고려",
                "리스크 관리를 위한 손절가 설정"
            ],
            recommendation="시장 변동성이 높은 상황에서 분할 매수/매도 전략을 권장합니다.",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


# 싱글톤 인스턴스
market_analyzer = MarketAnalyzer()


# 테스트
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("[Market Analyzer Test - Professional Version]")
    print("=" * 60)
    
    print("\n[AI Analysis]")
    print("-" * 40)
    
    analysis = market_analyzer.generate_analysis(["KODEX 코스닥150 레버리지"])
    
    print(f"\n[Summary]")
    print(f"  {analysis.summary}")
    
    print(f"\n[News Analysis]")
    print(f"  {analysis.news_analysis}")
    
    print(f"\n[Technical Summary]")
    print(f"  {analysis.technical_summary.overall}")
    
    print(f"\n[Market Sentiment]")
    print(f"  {analysis.market_sentiment}")
    
    print(f"\n[Hot Themes]")
    for theme in analysis.hot_themes:
        print(f"  - {theme.name}: {theme.reason}")
        print(f"    KOSPI: {theme.kospi_leader}, KOSDAQ: {theme.kosdaq_leader}")
    
    print(f"\n[Risk Factors]")
    for risk in analysis.risk_factors:
        print(f"  - {risk}")
    
    print(f"\n[Action Items]")
    for action in analysis.action_items:
        print(f"  - {action}")
    
    print(f"\n[Recommendation]")
    print(f"  {analysis.recommendation}")
    
    print(f"\n[Generated at: {analysis.generated_at}]")
    print("=" * 60)
