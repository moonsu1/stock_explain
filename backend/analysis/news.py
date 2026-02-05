# -*- coding: utf-8 -*-
"""
뉴스 크롤링 모듈
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_market_news(self, limit: int = 15) -> List[NewsItem]:
        """네이버 금융 실시간 뉴스"""
        news_list = []
        
        try:
            url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 링크 찾기 - news_read.naver 포함된 모든 a 태그
            all_links = soup.find_all("a", href=re.compile(r"news_read\.naver"))
            
            seen_titles = set()
            for link in all_links:
                try:
                    title = link.get_text(strip=True)
                    
                    # 제목 필터링
                    if not title or len(title) < 10:
                        continue
                    if title in seen_titles:
                        continue
                    
                    seen_titles.add(title)
                    
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = f"https://finance.naver.com{href}"
                    
                    # 직접 기사 링크로 변환
                    article_match = re.search(r'article_id=(\d+)', href)
                    office_match = re.search(r'office_id=(\d+)', href)
                    if article_match and office_match:
                        href = f"https://n.news.naver.com/mnews/article/{office_match.group(1)}/{article_match.group(1)}"
                    
                    # 부모 요소에서 시간 찾기
                    parent = link.find_parent("li") or link.find_parent("dd") or link.find_parent()
                    time_str = ""
                    source = "네이버금융"
                    
                    if parent:
                        parent_text = parent.get_text()
                        # 시간 파싱: HH:MM 형식
                        time_match = re.search(r'(\d{2}:\d{2})', parent_text)
                        if time_match:
                            time_str = time_match.group(1)
                        
                        # 출처 파싱: 한글|시간 형식
                        source_match = re.search(r'([가-힣]+)\s*\|?\s*\d{4}-\d{2}-\d{2}', parent_text)
                        if source_match:
                            source = source_match.group(1)
                    
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
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[Error] News crawling failed: {e}")
        
        # 뉴스가 없으면 백업 시도
        if not news_list:
            news_list = self._get_backup_news(limit)
        
        return news_list
    
    def _get_backup_news(self, limit: int = 15) -> List[NewsItem]:
        """백업: 네이버 뉴스 경제 섹션"""
        news_list = []
        
        try:
            url = "https://news.naver.com/section/101"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 뉴스 링크 찾기
            links = soup.select("a.sa_text_title, a[class*='title']")
            
            seen = set()
            for link in links[:limit]:
                try:
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10 or title in seen:
                        continue
                    
                    seen.add(title)
                    href = link.get("href", "")
                    
                    news_list.append(NewsItem(
                        title=title,
                        source="네이버뉴스",
                        time=datetime.now().strftime("%H:%M"),
                        url=href
                    ))
                except:
                    continue
                    
        except Exception as e:
            print(f"[Error] Backup news failed: {e}")
        
        return news_list
    
    def get_market_headlines(self) -> List[NewsItem]:
        """주요 시황 헤드라인"""
        return self.get_market_news(limit=15)
    
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
