"""
[TA/Research 역할] News Agent
- 웹 크롤링으로 AI 신기술 동향을 수집합니다
- Step 1: LLM으로 전체 목록에서 중요 뉴스 5개 번호 선별
- Step 2: 선별된 뉴스 5개를 각각 개별 LLM 호출로 충분히 요약
  (기존: 5개를 1번 호출로 몰아서 → 잘림 문제 발생)
"""

import re
from tools.web_search_tool import fetch_all_news
from agents.llm_client import call_llm
from prompts.templates import (
    NEWS_SUMMARY_SYSTEM,
    NEWS_SELECT_TEMPLATE,
    NEWS_ITEM_SUMMARY_TEMPLATE,
)


def _format_news_list_for_select(items: list[dict]) -> str:
    """번호 선별용 간략 목록 텍스트 생성"""
    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        source = item.get("source", "")
        lines.append(f"{i}. [{source}] {title}")
    return "\n".join(lines)


def _parse_selected_indices(llm_response: str, max_idx: int) -> list[int]:
    """LLM이 반환한 '3, 7, 12, ...' 형태에서 유효한 인덱스 파싱 (1-based → 0-based)"""
    nums = re.findall(r"\d+", llm_response)
    indices = []
    for n in nums:
        idx = int(n) - 1  # 0-based 변환
        if 0 <= idx < max_idx and idx not in indices:
            indices.append(idx)
        if len(indices) >= 5:
            break
    # 5개 못 찾으면 앞에서 채움
    if len(indices) < 5:
        for i in range(max_idx):
            if i not in indices:
                indices.append(i)
            if len(indices) >= 5:
                break
    return indices[:5]


def _summarize_single_news(item: dict) -> dict:
    """뉴스 아이템 1개를 LLM으로 개별 요약합니다."""
    title = item.get("title", "")
    source = item.get("source", "")
    content = item.get("summary", "") or title  # summary가 없으면 title로 대체

    user_prompt = NEWS_ITEM_SUMMARY_TEMPLATE.format(
        title=title,
        source=source,
        content=content[:800],
    )
    summary = call_llm(
        system_prompt=NEWS_SUMMARY_SYSTEM,
        user_prompt=user_prompt,
    )
    return {
        **item,
        "gemini_summary": summary,
    }


def run() -> list[dict]:
    """
    News Agent 메인 실행 함수.
    반환: 개별 요약이 완성된 뉴스 5개 (list[dict])
    """
    print("[News Agent] 웹 뉴스 수집 시작...")
    raw_items = fetch_all_news()

    if not raw_items:
        print("[News Agent] 수집된 뉴스 없음")
        return []

    # Step 1: 전체 목록에서 중요 뉴스 5개 번호 선별
    print(f"[News Agent] {len(raw_items)}개 뉴스 → 핵심 5개 선별 중...")
    news_list_str = _format_news_list_for_select(raw_items[:40])
    select_result = call_llm(
        system_prompt=NEWS_SUMMARY_SYSTEM,
        user_prompt=NEWS_SELECT_TEMPLATE.format(news_list=news_list_str),
    )
    selected_indices = _parse_selected_indices(select_result, len(raw_items[:40]))
    print(f"[News Agent] 선별된 뉴스 번호: {[i+1 for i in selected_indices]}")

    # Step 2: 선별된 뉴스 5개 개별 요약
    selected_news = [raw_items[i] for i in selected_indices]
    summarized = []
    for i, item in enumerate(selected_news, 1):
        print(f"  [뉴스 {i}/5] {item.get('title', '')[:55]}...")
        summarized.append(_summarize_single_news(item))

    print("[News Agent] 완료")
    return summarized
