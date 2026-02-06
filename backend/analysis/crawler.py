# -*- coding: utf-8 -*-
"""
네이버 금융 크롤러 (JSON API 버전)

안정적인 데이터 수집을 위해 네이버 모바일 금융 API를 사용합니다.
"""
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class IndexData:
    """지수 데이터"""
    name: str
    value: float
    change: float
    change_percent: float


def get_kospi_index() -> IndexData:
    """코스피 지수 조회 (네이버 JSON API)"""
    try:
        url = "https://m.stock.naver.com/api/index/KOSPI/basic"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # API 응답 구조: {"stockEndType":"index","compareToPreviousClosePrice":"...", ...}
        current_value = float(data.get("closePrice", "0").replace(",", ""))
        change = float(data.get("compareToPreviousClosePrice", "0").replace(",", ""))
        change_pct = float(data.get("fluctuationsRatio", "0").replace(",", ""))
        
        return IndexData(
            name="코스피",
            value=current_value,
            change=change,
            change_percent=change_pct
        )
    except Exception as e:
        print(f"[Error] KOSPI API failed: {e}")
        return IndexData("코스피", 0.0, 0.0, 0.0)


def get_kosdaq_index() -> IndexData:
    """코스닥 지수 조회 (네이버 JSON API)"""
    try:
        url = "https://m.stock.naver.com/api/index/KOSDAQ/basic"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current_value = float(data.get("closePrice", "0").replace(",", ""))
        change = float(data.get("compareToPreviousClosePrice", "0").replace(",", ""))
        change_pct = float(data.get("fluctuationsRatio", "0").replace(",", ""))
        
        return IndexData(
            name="코스닥",
            value=current_value,
            change=change,
            change_percent=change_pct
        )
    except Exception as e:
        print(f"[Error] KOSDAQ API failed: {e}")
        return IndexData("코스닥", 0.0, 0.0, 0.0)


def get_nasdaq_index() -> IndexData:
    """나스닥 지수 조회 (네이버 해외지수)"""
    from bs4 import BeautifulSoup
    import re
    
    try:
        # 네이버 금융 해외지수 페이지 크롤링
        url = "https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC"
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # 현재가
        value = 0.0
        today_elem = soup.select_one(".today")
        if today_elem:
            em_elem = today_elem.select_one("em")
            if em_elem:
                spans = em_elem.select("span")
                value_parts = []
                for span in spans:
                    text = span.get_text(strip=True)
                    if text and (text[0].isdigit() or text == "."):
                        value_parts.append(text)
                if value_parts:
                    value = float("".join(value_parts).replace(",", ""))
        
        # 전일대비, 등락률
        change = 0.0
        change_pct = 0.0
        
        exday_elem = soup.select_one(".no_exday")
        if exday_elem:
            text = exday_elem.get_text()
            numbers = re.findall(r'[\d,]+\.?\d*', text)
            if len(numbers) >= 1:
                change = float(numbers[0].replace(",", ""))
            if len(numbers) >= 2:
                change_pct = float(numbers[1].replace(",", ""))
            
            # 하락 여부
            if "down" in str(exday_elem) or "하락" in text:
                change = -abs(change)
                change_pct = -abs(change_pct)
        
        if value > 0:
            return IndexData("나스닥", value, change, change_pct)
            
    except Exception as e:
        print(f"[Error] NASDAQ crawl failed: {e}")
    
    return IndexData("나스닥", 0.0, 0.0, 0.0)


def get_all_indices() -> List[IndexData]:
    """모든 주요 지수 조회"""
    return [
        get_kospi_index(),
        get_kosdaq_index(),
        get_nasdaq_index()
    ]


def get_nikkei_index() -> IndexData:
    """니케이225 지수 조회 (네이버 해외지수 JPX@NI225)"""
    from bs4 import BeautifulSoup
    import re
    
    try:
        url = "https://finance.naver.com/world/sise.naver?symbol=JPX@NI225"
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "lxml")
        
        value = 0.0
        today_elem = soup.select_one(".today")
        if today_elem:
            em_elem = today_elem.select_one("em")
            if em_elem:
                spans = em_elem.select("span")
                value_parts = []
                for span in spans:
                    text = span.get_text(strip=True)
                    if text and (text[0].isdigit() or text == "."):
                        value_parts.append(text)
                if value_parts:
                    value = float("".join(value_parts).replace(",", ""))
        
        change = 0.0
        change_pct = 0.0
        
        exday_elem = soup.select_one(".no_exday")
        if exday_elem:
            text = exday_elem.get_text()
            numbers = re.findall(r'[\d,]+\.?\d*', text)
            if len(numbers) >= 1:
                change = float(numbers[0].replace(",", ""))
            if len(numbers) >= 2:
                change_pct = float(numbers[1].replace(",", ""))
            
            if "down" in str(exday_elem) or "하락" in text:
                change = -abs(change)
                change_pct = -abs(change_pct)
        
        if value > 0:
            return IndexData("니케이225", value, change, change_pct)
            
    except Exception as e:
        print(f"[Error] Nikkei crawl failed: {e}")
    
    return IndexData("니케이225", 0.0, 0.0, 0.0)


def get_commodity_price(code: str, name: str) -> IndexData:
    """원자재 시세 조회 (금, 은, 구리) - worldGoldDetail 동일 템플릿 사용"""
    from bs4 import BeautifulSoup
    import re
    
    try:
        url = f"https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd={code}"
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        html = response.text
        soup = BeautifulSoup(html, "lxml")
        
        # 현재가: .no_today .blind 우선, 없으면 .no_today 전체 텍스트에서 숫자 추출
        value = 0.0
        value_elem = soup.select_one(".no_today .blind")
        if value_elem:
            value = float(value_elem.get_text(strip=True).replace(",", ""))
        else:
            today_elem = soup.select_one(".no_today")
            if today_elem:
                nums = re.findall(r'[\d,]+\.?\d*', today_elem.get_text())
                if nums:
                    value = float(nums[0].replace(",", ""))
        
        # 전일대비·등락률: .no_exday .blind 우선, 없으면 .no_exday 전체에서 추출
        change = 0.0
        change_pct = 0.0
        change_elem = soup.select_one(".no_exday .blind")
        if change_elem:
            text = change_elem.get_text(strip=True)
            numbers = re.findall(r'[\d,]+\.?\d*', text)
            if numbers:
                change = float(numbers[0].replace(",", ""))
            if len(numbers) >= 2:
                change_pct = float(numbers[1].replace(",", ""))
        else:
            exday_elem = soup.select_one(".no_exday")
            if exday_elem:
                text = exday_elem.get_text()
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if len(numbers) >= 1:
                    change = float(numbers[0].replace(",", ""))
                if len(numbers) >= 2:
                    change_pct = float(numbers[1].replace(",", ""))
                if "down" in str(exday_elem) or "하락" in text or "minus" in str(exday_elem).lower():
                    change = -abs(change)
                    change_pct = -abs(change_pct) if change_pct else change_pct
        
        # 등락 방향 (blind 없을 때)
        down_elem = soup.select_one(".no_exday.down, .no_exday .ico.down")
        if down_elem or (soup.select_one(".no_exday") and "down" in str(soup.select_one(".no_exday"))):
            change = -abs(change)
            if change_pct and change_pct > 0:
                change_pct = -abs(change_pct)
        
        if value > 0 and change_pct == 0 and change != 0:
            change_pct = (change / (value - change)) * 100
        
        if value > 0:
            return IndexData(name, value, change, change_pct)
            
    except Exception as e:
        print(f"[Error] Commodity crawl failed ({name}): {e}")
    
    return IndexData(name, 0.0, 0.0, 0.0)


def get_gold_price() -> IndexData:
    """금 시세 (COMEX)"""
    return get_commodity_price("CMDT_GC", "금")


def get_silver_price() -> IndexData:
    """은 시세 (COMEX)"""
    return get_commodity_price("CMDT_SI", "은")


def get_copper_price() -> IndexData:
    """구리 시세 (COMEX)"""
    return get_commodity_price("CMDT_HG", "구리")


def get_commodities_and_world() -> List[IndexData]:
    """원자재 및 해외 지수 조회"""
    return [
        get_nikkei_index(),
        get_gold_price(),
        get_silver_price(),
        get_copper_price()
    ]


def get_stock_price(code: str) -> Optional[Dict[str, Any]]:
    """개별 종목 시세 조회 (네이버 JSON API)"""
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/basic"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 종목명
        name = data.get("stockName", "Unknown")
        
        # 현재가
        current_price = int(data.get("closePrice", "0").replace(",", ""))
        
        # 전일대비
        change = int(data.get("compareToPreviousClosePrice", "0").replace(",", ""))
        
        # 등락률
        change_pct = float(data.get("fluctuationsRatio", "0").replace(",", ""))
        
        # 거래량
        volume = int(data.get("accumulatedTradingVolume", "0").replace(",", ""))
        
        return {
            "code": code,
            "name": name,
            "currentPrice": current_price,
            "change": change,
            "changePercent": change_pct,
            "volume": volume
        }
        
    except Exception as e:
        print(f"[Error] Stock API failed ({code}): {e}")
        return None


def get_stock_basic_info(code: str) -> Optional[Dict[str, Any]]:
    """종목 기본 정보 조회"""
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/integration"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
    except Exception as e:
        print(f"[Error] Stock info API failed ({code}): {e}")
        return None


# 테스트
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 50)
    print("[Market Data Test - Naver JSON API]")
    print("=" * 50)
    
    print("\n[Major Indices]")
    print("-" * 40)
    for idx in get_all_indices():
        sign = "+" if idx.change >= 0 else ""
        status = "(up)" if idx.change >= 0 else "(down)"
        print(f"  {idx.name}: {idx.value:,.2f}  {status} {sign}{idx.change:,.2f} ({sign}{idx.change_percent:.2f}%)")
    
    print("\n[Stock Prices]")
    print("-" * 40)
    test_stocks = ["233740", "005930", "000660"]
    for code in test_stocks:
        stock = get_stock_price(code)
        if stock:
            sign = "+" if stock['change'] >= 0 else ""
            print(f"  {stock['name']}: {stock['currentPrice']:,}won  {sign}{stock['change']:,} ({sign}{stock['changePercent']:.2f}%)")
        else:
            print(f"  {code}: Failed to fetch")
    
    print("\n" + "=" * 50)
    print("[Test Complete]")
