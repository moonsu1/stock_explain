"""
웹 크롤링 툴
- HuggingFace Papers 일별 인기 논문
- VentureBeat AI 섹션 최신 기사
- Google News RSS 피드 (키워드별)
"""

import feedparser
import requests
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from config import NEWS_SOURCES, GOOGLE_NEWS_RSS_KEYWORDS, GOOGLE_NEWS_RSS_BASE, NEWS_MAX_AGE_DAYS


def _is_recent(published_str: str, max_age_days: int = NEWS_MAX_AGE_DAYS) -> bool:
    """RSS published 날짜 문자열이 max_age_days 이내인지 확인합니다."""
    if not published_str:
        return True  # 날짜 없으면 일단 통과
    try:
        pub_dt = parsedate_to_datetime(published_str)
        # timezone-aware로 변환
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        return pub_dt >= cutoff
    except Exception:
        return True  # 파싱 실패 시 통과

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_huggingface_papers(max_items: int = 10) -> list[dict]:
    """HuggingFace Papers에서 오늘의 인기 논문 제목·URL을 수집합니다."""
    try:
        resp = requests.get(NEWS_SOURCES["huggingface_papers"], headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        items = []
        for article in soup.select("article")[:max_items]:
            title_tag = article.find("h3") or article.find("h2")
            link_tag = article.find("a", href=True)
            if not title_tag or not link_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = link_tag["href"]
            url = href if href.startswith("http") else f"https://huggingface.co{href}"
            if title:
                items.append({"source": "HuggingFace Papers", "title": title, "url": url})

        return items
    except Exception as e:
        print(f"  [web] HuggingFace Papers 크롤링 실패: {e}")
        return []


def fetch_venturebeat_ai(max_items: int = 8) -> list[dict]:
    """VentureBeat AI 섹션 최신 기사를 수집합니다 (60일 이내만)."""
    rss_url = "https://venturebeat.com/category/ai/feed/"
    try:
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries:
            if len(items) >= max_items:
                break
            published = entry.get("published", "")
            if not _is_recent(published):
                continue
            items.append({
                "source": "VentureBeat AI",
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": published,
            })
        return items
    except Exception as e:
        print(f"  [web] VentureBeat RSS 수집 실패: {e}")
        return []


def fetch_google_news_rss(keyword: str, max_items: int = 5) -> list[dict]:
    """Google News RSS에서 특정 키워드 뉴스를 수집합니다 (60일 이내만)."""
    # Google News RSS에 날짜 필터 파라미터 추가 (after:YYYY-MM-DD)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=NEWS_MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    filtered_keyword = f"{keyword} after:{cutoff_date}"
    url = GOOGLE_NEWS_RSS_BASE.format(query=quote_plus(filtered_keyword))
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            if len(items) >= max_items:
                break
            published = entry.get("published", "")
            if not _is_recent(published):
                continue
            items.append({
                "source": f"Google News ({keyword})",
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": published,
            })
        return items
    except Exception as e:
        print(f"  [web] Google News RSS ({keyword}) 수집 실패: {e}")
        return []


def fetch_all_news() -> list[dict]:
    """
    모든 뉴스 소스를 수집해서 합칩니다.
    반환값: [{"source", "title", "url", ...}, ...]
    """
    all_items: list[dict] = []

    print("  [web] HuggingFace Papers 수집 중...")
    all_items.extend(fetch_huggingface_papers())
    time.sleep(1)

    print("  [web] VentureBeat AI 수집 중...")
    all_items.extend(fetch_venturebeat_ai())
    time.sleep(1)

    print("  [web] Google News RSS 수집 중...")
    for keyword in GOOGLE_NEWS_RSS_KEYWORDS:
        all_items.extend(fetch_google_news_rss(keyword, max_items=3))
        time.sleep(0.5)

    print(f"  [web] 총 {len(all_items)}개 뉴스 아이템 수집 완료")
    return all_items
