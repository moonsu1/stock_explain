"""
arxiv 논문 수집 툴
- 키워드 그룹별로 최신 논문을 수집합니다
- 중복 논문(같은 arxiv ID)을 제거합니다
"""

import arxiv
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from config import ARXIV_KEYWORD_GROUPS, MAX_PAPERS_PER_GROUP


def fetch_papers_by_keyword(
    keyword: str,
    max_results: int = 5,
    days_back: int = 3,
) -> list[dict]:
    """단일 키워드로 최신 논문을 수집합니다."""
    client = arxiv.Client()
    search = arxiv.Search(
        query=keyword,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    papers = []

    for result in client.results(search):
        submitted = result.published
        if submitted < cutoff:
            break
        papers.append({
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "abstract": result.summary,
            "authors": [a.name for a in result.authors[:3]],
            "url": result.entry_id,
            "published": submitted.strftime("%Y-%m-%d"),
            "categories": result.categories,
        })

    return papers


def fetch_papers_for_group(
    group_key: str,
    days_back: int = 3,
) -> list[dict]:
    """
    키워드 그룹 전체를 순회하며 논문을 수집하고,
    중복을 제거한 뒤 MAX_PAPERS_PER_GROUP 편을 반환합니다.
    """
    group = ARXIV_KEYWORD_GROUPS.get(group_key)
    if not group:
        return []

    seen_ids: set[str] = set()
    collected: list[dict] = []

    for keyword in group["keywords"]:
        if len(collected) >= MAX_PAPERS_PER_GROUP:
            break

        papers = fetch_papers_by_keyword(
            keyword=keyword,
            max_results=MAX_PAPERS_PER_GROUP * 2,
            days_back=days_back,
        )

        for paper in papers:
            if paper["id"] not in seen_ids:
                seen_ids.add(paper["id"])
                paper["group_key"] = group_key
                paper["group_label"] = group["label"]
                paper["group_emoji"] = group["emoji"]
                collected.append(paper)

            if len(collected) >= MAX_PAPERS_PER_GROUP:
                break

        time.sleep(0.5)

    return collected[:MAX_PAPERS_PER_GROUP]


def fetch_all_groups(days_back: int = 3) -> dict[str, list[dict]]:
    """
    모든 키워드 그룹의 논문을 수집합니다.
    반환값: { group_key: [paper, ...], ... }
    """
    result: dict[str, list[dict]] = {}
    for group_key in ARXIV_KEYWORD_GROUPS:
        print(f"  [arxiv] '{group_key}' 그룹 수집 중...")
        papers = fetch_papers_for_group(group_key, days_back=days_back)
        result[group_key] = papers
        print(f"  [arxiv] '{group_key}' → {len(papers)}편 수집 완료")
        time.sleep(1)
    return result
