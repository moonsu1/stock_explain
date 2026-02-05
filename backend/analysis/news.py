# -*- coding: utf-8 -*-
"""
뉴스 크롤링 모듈

여러 금융 뉴스 소스에서 실시간 증시 뉴스를 수집합니다.
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
    """뉴스 크롤러 - 여러 소스 지원"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_market_headlines(self) -> List[NewsItem]:
        """주요 시황 헤드라인 (여러 소스 통합)"""
        all_news = []
        
        # 1. 네이버 금융 주요뉴스 (가장 신뢰할 수 있는 소스)
        naver_news = self._get_naver_main_news()
        all_news.extend(naver_news)
        
        # 2. 한국경제 증권 뉴스
        hankyung_news = self._get_hankyung_news()
        all_news.extend(hankyung_news)
        
        # 3. 매일경제 증권 뉴스
        mk_news = self._get_mk_news()
        all_news.extend(mk_news)
        
        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_news = []
        for news in all_news:
            # 제목에서 특수문자 제거 후 비교
            clean_title = re.sub(r'[^\w\s]', '', news.title)[:30]
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                unique_news.append(news)
        
        return unique_news[:15]
    
    def _get_naver_main_news(self) -> List[NewsItem]:
        """네이버 금융 주요뉴스"""
        news_list = []
        
        try:
            # 주요뉴스 페이지
            url = "https://finance.naver.com/news/mainnews.naver"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 목록 파싱
            items = soup.select(".mainNewsList li, .newsList li")
            
            for item in items[:10]:
                try:
                    link = item.select_one("a")
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    href = link.get("href", "")
                    if not href or "news_read" not in href:
                        continue
                    
                    # 절대 URL 변환
                    if not href.startswith("http"):
                        href = f"https://finance.naver.com{href}"
                    
                    # 직접 기사 링크로 변환
                    article_match = re.search(r'article_id=(\d+)', href)
                    office_match = re.search(r'office_id=(\d+)', href)
                    if article_match and office_match:
                        href = f"https://n.news.naver.com/mnews/article/{office_match.group(1)}/{article_match.group(1)}"
                    
                    # 출처 추출
                    source = "네이버금융"
                    source_elem = item.select_one(".press, .info")
                    if source_elem:
                        source = source_elem.get_text(strip=True).split("|")[0].strip()
                    
                    # 시간 추출
                    time_str = datetime.now().strftime("%H:%M")
                    dd_elem = item.select_one("dd")
                    if dd_elem:
                        text = dd_elem.get_text()
                        time_match = re.search(r'(\d{2}:\d{2})', text)
                        if time_match:
                            time_str = time_match.group(1)
                    
                    news_list.append(NewsItem(
                        title=title,
                        source=source,
                        time=time_str,
                        url=href
                    ))
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[Error] Naver main news failed: {e}")
        
        return news_list
    
    def _get_hankyung_news(self) -> List[NewsItem]:
        """한국경제 증권 뉴스"""
        news_list = []
        
        try:
            url = "https://www.hankyung.com/finance/stock"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 목록 파싱
            items = soup.select(".news-tit a, .article-list a, .news-item a")
            
            seen = set()
            for item in items[:8]:
                try:
                    title = item.get_text(strip=True)
                    if not title or len(title) < 10 or title in seen:
                        continue
                    
                    seen.add(title)
                    href = item.get("href", "")
                    if not href.startswith("http"):
                        href = f"https://www.hankyung.com{href}"
                    
                    news_list.append(NewsItem(
                        title=title,
                        source="한국경제",
                        time=datetime.now().strftime("%H:%M"),
                        url=href
                    ))
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[Error] Hankyung news failed: {e}")
        
        return news_list
    
    def _get_mk_news(self) -> List[NewsItem]:
        """매일경제 증권 뉴스"""
        news_list = []
        
        try:
            url = "https://www.mk.co.kr/news/stock/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 목록 파싱
            items = soup.select(".news_ttl a, .article_title a, .news_node a")
            
            seen = set()
            for item in items[:8]:
                try:
                    title = item.get_text(strip=True)
                    if not title or len(title) < 10 or title in seen:
                        continue
                    
                    seen.add(title)
                    href = item.get("href", "")
                    if not href.startswith("http"):
                        href = f"https://www.mk.co.kr{href}"
                    
                    news_list.append(NewsItem(
                        title=title,
                        source="매일경제",
                        time=datetime.now().strftime("%H:%M"),
                        url=href
                    ))
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[Error] MK news failed: {e}")
        
        return news_list
    
    def get_market_news(self, limit: int = 15) -> List[NewsItem]:
        """시장 뉴스 (get_market_headlines 래퍼)"""
        return self.get_market_headlines()[:limit]
    
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
                    
                    # 직접 기사 링크로 변환
                    if "article_id=" in href and "office_id=" in href:
                        article_match = re.search(r'article_id=(\d+)', href)
                        office_match = re.search(r'office_id=(\d+)', href)
                        if article_match and office_match:
                            href = f"https://n.news.naver.com/mnews/article/{office_match.group(1)}/{article_match.group(1)}"
                    
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
