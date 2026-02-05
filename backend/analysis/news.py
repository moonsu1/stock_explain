# -*- coding: utf-8 -*-
"""
뉴스 크롤링 모듈

네이버 금융에서 실시간 증시 뉴스를 수집합니다.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class NewsItem:
    """뉴스 아이템"""
    title: str
    source: str
    time: str
    url: str
    summary: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class NewsCrawler:
    """뉴스 크롤러"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_market_news(self, limit: int = 15) -> List[NewsItem]:
        """시장 뉴스 크롤링 (네이버 금융 뉴스)"""
        news_list = []
        
        try:
            # 네이버 금융 뉴스 목록
            url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 목록 파싱 - 다양한 셀렉터 시도
            news_items = soup.select("dd") or soup.select(".articleSubject a") or soup.select(".block1 li")
            
            for item in news_items:
                try:
                    # 링크 찾기
                    if item.name == "a":
                        title_link = item
                    else:
                        title_link = item.select_one("a")
                    
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    # 제목이 너무 짧으면 스킵
                    if not title or len(title) < 5:
                        continue
                    
                    href = title_link.get("href", "")
                    
                    # 절대 URL로 변환
                    if href and not href.startswith("http"):
                        if href.startswith("/"):
                            href = f"https://finance.naver.com{href}"
                        else:
                            href = f"https://finance.naver.com/{href}"
                    
                    # 출처와 시간
                    source = "네이버금융"
                    time_str = ""
                    
                    # 시간 찾기
                    time_elem = item.select_one(".wdate") or item.select_one(".time") or item.select_one("span")
                    if time_elem:
                        time_str = time_elem.get_text(strip=True)
                    
                    if not time_str:
                        time_str = datetime.now().strftime("%H:%M")
                    
                    news_list.append(NewsItem(
                        title=title,
                        source=source,
                        time=time_str,
                        url=href
                    ))
                    
                    if len(news_list) >= limit:
                        break
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"[Error] News crawling failed: {e}")
        
        # 뉴스가 부족하면 추가 시도
        if len(news_list) < 5:
            more_news = self._get_breaking_news(limit - len(news_list))
            news_list.extend(more_news)
        
        return news_list
    
    def _get_breaking_news(self, limit: int = 15) -> List[NewsItem]:
        """실시간 속보 뉴스"""
        news_list = []
        
        try:
            url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 리스트
            items = soup.select(".realtimeNewsList li, .newsList li, dd")
            
            for item in items[:limit]:
                try:
                    link = item.select_one("a")
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    href = link.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://finance.naver.com{href}"
                    
                    # 시간 추출
                    time_elem = item.select_one(".time, .wdate, span")
                    time_str = time_elem.get_text(strip=True) if time_elem else ""
                    if not time_str:
                        time_str = datetime.now().strftime("%H:%M")
                    
                    news_list.append(NewsItem(
                        title=title,
                        source="네이버금융",
                        time=time_str,
                        url=href
                    ))
                except:
                    continue
                    
        except Exception as e:
            print(f"[Error] Breaking news failed: {e}")
        
        return news_list
    
    def get_stock_news(self, stock_code: str, limit: int = 10) -> List[NewsItem]:
        """특정 종목 관련 뉴스"""
        news_list = []
        
        try:
            url = f"https://finance.naver.com/item/news_news.naver?code={stock_code}&page=1"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            rows = soup.select("table.type5 tr")
            
            for row in rows[:limit]:
                try:
                    cols = row.select("td")
                    if len(cols) < 3:
                        continue
                    
                    title_link = cols[0].select_one("a")
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    href = title_link.get("href", "")
                    
                    if href and not href.startswith("http"):
                        href = f"https://finance.naver.com{href}"
                    
                    source = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    time_str = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    
                    news_list.append(NewsItem(
                        title=title,
                        source=source,
                        time=time_str,
                        url=href
                    ))
                except:
                    continue
                    
        except Exception as e:
            print(f"[Error] Stock news failed ({stock_code}): {e}")
        
        return news_list
    
    def get_market_headlines(self) -> List[NewsItem]:
        """주요 시황 헤드라인 (메인 함수)"""
        news = self.get_market_news(limit=15)
        
        if not news:
            # 최후의 수단: 직접 네이버 뉴스 증권 섹션
            news = self._get_naver_finance_section()
        
        return news
    
    def _get_naver_finance_section(self) -> List[NewsItem]:
        """네이버 뉴스 증권 섹션"""
        news_list = []
        
        try:
            url = "https://news.naver.com/section/101"  # 경제 섹션
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 헤드라인 뉴스
            items = soup.select(".sa_text a, .sa_item a")
            
            seen_titles = set()
            for item in items:
                try:
                    title = item.get_text(strip=True)
                    if not title or len(title) < 10 or title in seen_titles:
                        continue
                    
                    seen_titles.add(title)
                    href = item.get("href", "")
                    
                    news_list.append(NewsItem(
                        title=title,
                        source="네이버뉴스",
                        time=datetime.now().strftime("%H:%M"),
                        url=href
                    ))
                    
                    if len(news_list) >= 15:
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[Error] Naver news section failed: {e}")
        
        return news_list


# 싱글톤 인스턴스
news_crawler = NewsCrawler()


# 테스트
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("[News Crawling Test]")
    print("=" * 60)
    
    print("\n[Market Headlines]")
    print("-" * 60)
    
    news = news_crawler.get_market_headlines()
    for i, n in enumerate(news[:10], 1):
        print(f"{i}. [{n.source}] {n.title}")
        print(f"   Time: {n.time}")
        print(f"   URL: {n.url}")
        print()
    
    print("=" * 60)
    print(f"[Total: {len(news)} news items]")
