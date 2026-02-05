# -*- coding: utf-8 -*-
"""
기술적 지표 분석 모듈

RSI, 볼린저밴드, 이동평균선 등 기술적 지표를 계산합니다.
"""
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.naver.com/",
}

# 분석 대상 종목
DEFAULT_STOCKS = {
    # 지수 ETF
    "069500": "KODEX 200",
    "229200": "KODEX 코스닥150",
    # 시총 상위
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "373220": "LG에너지솔루션",
}


@dataclass
class TechnicalIndicators:
    """기술적 지표 데이터"""
    code: str
    name: str
    current_price: float
    # RSI
    rsi: float
    rsi_status: str  # 과매수/과매도/중립
    # 볼린저밴드
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_status: str  # 상단돌파/하단이탈/밴드내
    bb_width: float  # 밴드폭 (변동성)
    # 이동평균선
    ma5: float
    ma20: float
    ma60: float
    ma120: float
    ma_status: str  # 정배열/역배열/혼조
    # 추세
    trend: str  # 상승/하락/횡보
    golden_cross: bool  # 골든크로스 발생
    dead_cross: bool  # 데드크로스 발생
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_stock_ohlcv(code: str, days: int = 150) -> Optional[pd.DataFrame]:
    """
    네이버 금융에서 일봉 데이터 가져오기
    
    Args:
        code: 종목코드
        days: 가져올 일수 (기본 150일, 120일 이동평균 계산 위해)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    try:
        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # 여유분
        
        url = "https://api.finance.naver.com/siseJson.naver"
        params = {
            "symbol": code,
            "requestType": "1",
            "startTime": start_date.strftime("%Y%m%d"),
            "endTime": end_date.strftime("%Y%m%d"),
            "timeframe": "day"
        }
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # 응답 파싱 (JSON 형식이지만 따옴표가 없는 형태)
        text = response.text.strip()
        # 줄바꿈, 탭 정리
        text = text.replace("\n", "").replace("\t", "")
        
        # eval로 파싱 (주의: 신뢰할 수 있는 소스에서만 사용)
        import ast
        try:
            data = ast.literal_eval(text)
        except:
            # 대안: JSON으로 변환 시도
            import json
            import re
            # 작은따옴표를 큰따옴표로 변환
            text = re.sub(r"'", '"', text)
            data = json.loads(text)
        
        if not data or len(data) < 2:
            print(f"[Warning] No OHLCV data for {code}")
            return None
        
        # 첫 행은 컬럼명
        columns = data[0]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=columns)
        
        # 컬럼명 정리 (한글 -> 영문)
        column_map = {
            "날짜": "date",
            "시가": "open",
            "고가": "high",
            "저가": "low",
            "종가": "close",
            "거래량": "volume",
        }
        df = df.rename(columns=column_map)
        
        # 필요한 컬럼만 선택
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        available_cols = [c for c in required_cols if c in df.columns]
        df = df[available_cols]
        
        # 데이터 타입 변환
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # 날짜 정렬 (오래된 순)
        df = df.sort_values("date").reset_index(drop=True)
        
        # 최근 days일만
        df = df.tail(days).reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"[Error] Failed to get OHLCV for {code}: {e}")
        return None


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI (Relative Strength Index) 계산"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """볼린저밴드 계산"""
    middle = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    width = (upper - lower) / middle * 100  # 밴드폭 (%)
    
    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "width": width
    }


def calculate_moving_averages(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """이동평균선 계산"""
    return {
        "ma5": df["close"].rolling(window=5).mean(),
        "ma20": df["close"].rolling(window=20).mean(),
        "ma60": df["close"].rolling(window=60).mean(),
        "ma120": df["close"].rolling(window=120).mean(),
    }


def get_rsi_status(rsi: float) -> str:
    """RSI 상태 판단"""
    if rsi >= 70:
        return "과매수"
    elif rsi <= 30:
        return "과매도"
    elif rsi >= 60:
        return "매수우위"
    elif rsi <= 40:
        return "매도우위"
    else:
        return "중립"


def get_bb_status(price: float, upper: float, middle: float, lower: float) -> str:
    """볼린저밴드 상태 판단"""
    if price > upper:
        return "상단돌파"
    elif price < lower:
        return "하단이탈"
    elif price > middle:
        return "상단접근"
    elif price < middle:
        return "하단접근"
    else:
        return "중심선"


def get_ma_status(ma5: float, ma20: float, ma60: float, ma120: float) -> str:
    """이동평균선 배열 상태 판단"""
    if ma5 > ma20 > ma60 > ma120:
        return "정배열"
    elif ma5 < ma20 < ma60 < ma120:
        return "역배열"
    elif ma5 > ma20 and ma20 > ma60:
        return "단기상승"
    elif ma5 < ma20 and ma20 < ma60:
        return "단기하락"
    else:
        return "혼조"


def get_trend(price: float, ma20: float, ma60: float, rsi: float) -> str:
    """추세 판단"""
    above_ma20 = price > ma20
    above_ma60 = price > ma60
    
    if above_ma20 and above_ma60 and rsi > 50:
        return "상승추세"
    elif not above_ma20 and not above_ma60 and rsi < 50:
        return "하락추세"
    else:
        return "횡보"


def check_cross(ma_short: pd.Series, ma_long: pd.Series) -> Dict[str, bool]:
    """골든크로스/데드크로스 확인 (최근 5일 내)"""
    recent_short = ma_short.tail(5)
    recent_long = ma_long.tail(5)
    
    golden_cross = False
    dead_cross = False
    
    for i in range(1, len(recent_short)):
        prev_diff = recent_short.iloc[i-1] - recent_long.iloc[i-1]
        curr_diff = recent_short.iloc[i] - recent_long.iloc[i]
        
        if prev_diff < 0 and curr_diff > 0:
            golden_cross = True
        elif prev_diff > 0 and curr_diff < 0:
            dead_cross = True
    
    return {"golden_cross": golden_cross, "dead_cross": dead_cross}


def analyze_stock(code: str, name: str = None) -> Optional[TechnicalIndicators]:
    """
    개별 종목 기술적 분석
    
    Args:
        code: 종목코드
        name: 종목명 (없으면 DEFAULT_STOCKS에서 조회)
    
    Returns:
        TechnicalIndicators 객체
    """
    if name is None:
        name = DEFAULT_STOCKS.get(code, code)
    
    # 일봉 데이터 가져오기
    df = get_stock_ohlcv(code)
    if df is None or len(df) < 120:
        print(f"[Warning] Insufficient data for {code}")
        return None
    
    # 현재가
    current_price = df["close"].iloc[-1]
    
    # RSI 계산
    rsi_series = calculate_rsi(df)
    rsi = rsi_series.iloc[-1]
    rsi_status = get_rsi_status(rsi)
    
    # 볼린저밴드 계산
    bb = calculate_bollinger_bands(df)
    bb_upper = bb["upper"].iloc[-1]
    bb_middle = bb["middle"].iloc[-1]
    bb_lower = bb["lower"].iloc[-1]
    bb_width = bb["width"].iloc[-1]
    bb_status = get_bb_status(current_price, bb_upper, bb_middle, bb_lower)
    
    # 이동평균선 계산
    ma = calculate_moving_averages(df)
    ma5 = ma["ma5"].iloc[-1]
    ma20 = ma["ma20"].iloc[-1]
    ma60 = ma["ma60"].iloc[-1]
    ma120 = ma["ma120"].iloc[-1]
    ma_status = get_ma_status(ma5, ma20, ma60, ma120)
    
    # 추세 판단
    trend = get_trend(current_price, ma20, ma60, rsi)
    
    # 골든/데드크로스 확인
    cross = check_cross(ma["ma5"], ma["ma20"])
    
    return TechnicalIndicators(
        code=code,
        name=name,
        current_price=current_price,
        rsi=round(rsi, 2),
        rsi_status=rsi_status,
        bb_upper=round(bb_upper, 2),
        bb_middle=round(bb_middle, 2),
        bb_lower=round(bb_lower, 2),
        bb_status=bb_status,
        bb_width=round(bb_width, 2),
        ma5=round(ma5, 2),
        ma20=round(ma20, 2),
        ma60=round(ma60, 2),
        ma120=round(ma120, 2),
        ma_status=ma_status,
        trend=trend,
        golden_cross=cross["golden_cross"],
        dead_cross=cross["dead_cross"],
    )


def analyze_multiple_stocks(codes: List[str] = None) -> List[TechnicalIndicators]:
    """
    여러 종목 기술적 분석
    
    Args:
        codes: 종목코드 리스트 (없으면 DEFAULT_STOCKS 사용)
    
    Returns:
        TechnicalIndicators 리스트
    """
    if codes is None:
        codes = list(DEFAULT_STOCKS.keys())
    
    results = []
    for code in codes:
        name = DEFAULT_STOCKS.get(code, code)
        print(f"[Info] Analyzing {name} ({code})...")
        
        indicators = analyze_stock(code, name)
        if indicators:
            results.append(indicators)
        
        # Rate limiting
        time.sleep(0.5)
    
    return results


def get_market_technical_summary(indicators: List[TechnicalIndicators]) -> Dict[str, Any]:
    """
    전체 시장 기술적 지표 요약
    
    Args:
        indicators: TechnicalIndicators 리스트
    
    Returns:
        시장 전체 요약 딕셔너리
    """
    if not indicators:
        return {
            "overall": "데이터 부족",
            "avg_rsi": 50,
            "oversold_count": 0,
            "overbought_count": 0,
            "uptrend_count": 0,
            "downtrend_count": 0,
            "golden_cross_stocks": [],
            "dead_cross_stocks": [],
        }
    
    # 평균 RSI
    avg_rsi = sum(i.rsi for i in indicators) / len(indicators)
    
    # 과매도/과매수 종목 수
    oversold = [i for i in indicators if i.rsi <= 30]
    overbought = [i for i in indicators if i.rsi >= 70]
    
    # 추세별 종목 수
    uptrend = [i for i in indicators if i.trend == "상승추세"]
    downtrend = [i for i in indicators if i.trend == "하락추세"]
    
    # 크로스 발생 종목
    golden_cross_stocks = [i.name for i in indicators if i.golden_cross]
    dead_cross_stocks = [i.name for i in indicators if i.dead_cross]
    
    # 전체 시장 판단
    if avg_rsi >= 70:
        overall = "과매수 구간 - 조정 가능성"
    elif avg_rsi <= 30:
        overall = "과매도 구간 - 반등 가능성"
    elif len(uptrend) > len(downtrend) * 2:
        overall = "상승 우위 - 매수 관점 유리"
    elif len(downtrend) > len(uptrend) * 2:
        overall = "하락 우위 - 관망 또는 방어적 접근"
    else:
        overall = "혼조세 - 종목별 선별 접근"
    
    return {
        "overall": overall,
        "avg_rsi": round(avg_rsi, 2),
        "oversold_count": len(oversold),
        "overbought_count": len(overbought),
        "oversold_stocks": [i.name for i in oversold],
        "overbought_stocks": [i.name for i in overbought],
        "uptrend_count": len(uptrend),
        "downtrend_count": len(downtrend),
        "golden_cross_stocks": golden_cross_stocks,
        "dead_cross_stocks": dead_cross_stocks,
    }


def format_technical_for_prompt(indicators: List[TechnicalIndicators]) -> str:
    """
    GPT 프롬프트용 기술적 지표 텍스트 생성
    
    Args:
        indicators: TechnicalIndicators 리스트
    
    Returns:
        프롬프트에 포함할 텍스트
    """
    if not indicators:
        return "기술적 지표 데이터 없음"
    
    summary = get_market_technical_summary(indicators)
    
    lines = [
        f"## 기술적 지표 분석",
        f"- 시장 종합: {summary['overall']}",
        f"- 평균 RSI: {summary['avg_rsi']} (30이하 과매도, 70이상 과매수)",
        f"- 과매도 종목: {summary['oversold_count']}개 ({', '.join(summary['oversold_stocks']) if summary['oversold_stocks'] else '없음'})",
        f"- 과매수 종목: {summary['overbought_count']}개 ({', '.join(summary['overbought_stocks']) if summary['overbought_stocks'] else '없음'})",
        f"- 상승추세 종목: {summary['uptrend_count']}개, 하락추세 종목: {summary['downtrend_count']}개",
    ]
    
    if summary['golden_cross_stocks']:
        lines.append(f"- 골든크로스 발생: {', '.join(summary['golden_cross_stocks'])}")
    if summary['dead_cross_stocks']:
        lines.append(f"- 데드크로스 발생: {', '.join(summary['dead_cross_stocks'])}")
    
    lines.append("\n### 종목별 상세")
    for ind in indicators:
        lines.append(
            f"- {ind.name}: RSI {ind.rsi}({ind.rsi_status}), "
            f"볼린저 {ind.bb_status}, 이평선 {ind.ma_status}, 추세 {ind.trend}"
        )
    
    return "\n".join(lines)


# 테스트
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("[Technical Indicators Test]")
    print("=" * 60)
    
    # 단일 종목 테스트
    print("\n[Single Stock Analysis: Samsung Electronics]")
    result = analyze_stock("005930", "삼성전자")
    if result:
        print(f"  Current Price: {result.current_price:,}")
        print(f"  RSI: {result.rsi} ({result.rsi_status})")
        print(f"  Bollinger: {result.bb_status} (width: {result.bb_width}%)")
        print(f"  MA Status: {result.ma_status}")
        print(f"  Trend: {result.trend}")
        print(f"  Golden Cross: {result.golden_cross}, Dead Cross: {result.dead_cross}")
    
    # 여러 종목 테스트
    print("\n[Multiple Stocks Analysis]")
    indicators = analyze_multiple_stocks()
    
    # 요약
    summary = get_market_technical_summary(indicators)
    print(f"\n[Market Summary]")
    print(f"  Overall: {summary['overall']}")
    print(f"  Avg RSI: {summary['avg_rsi']}")
    
    # 프롬프트용 텍스트
    print("\n[Prompt Text]")
    print("-" * 40)
    print(format_technical_for_prompt(indicators))
