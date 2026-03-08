"""
[TA/Research 역할] Paper Agent
- arxiv에서 5개 그룹별 최신 논문을 수집합니다
- 각 논문의 초록을 LLM으로 요약합니다 (삼성리서치 파트별 관점)
"""

from tools.arxiv_tool import fetch_all_groups
from agents.llm_client import call_llm
from prompts.templates import PAPER_SUMMARY_SYSTEM, PAPER_SUMMARY_USER_TEMPLATE
from config import ARXIV_KEYWORD_GROUPS

# 각 그룹의 짧은 팀 관점 레이블 (프롬프트 내 {perspective_short} 대체용)
PERSPECTIVE_SHORT = {
    "agent_system":    "Agent System / LLM 학습",
    "web_agent":       "Web Agent / GUI Agent",
    "generative_ui":   "Generative UI",
    "knowledge_graph": "Knowledge Graph + LLM 융합",
}


def summarize_paper(paper: dict) -> dict:
    """단일 논문을 LLM으로 요약합니다."""
    group_key = paper.get("group_key", "")
    group = ARXIV_KEYWORD_GROUPS.get(group_key, {})
    perspective = group.get("perspective", "AI 엔지니어 관점에서 이 논문이 왜 중요한지 설명해주세요.")
    perspective_short = PERSPECTIVE_SHORT.get(group_key, "AI 연구")

    user_prompt = PAPER_SUMMARY_USER_TEMPLATE.format(
        perspective=perspective,
        perspective_short=perspective_short,
        title=paper["title"],
        authors=", ".join(paper.get("authors", [])),
        abstract=paper["abstract"][:2000],
    )

    summary = call_llm(
        system_prompt=PAPER_SUMMARY_SYSTEM,
        user_prompt=user_prompt,
    )

    return {**paper, "gemini_summary": summary}


def run(days_back: int = 3) -> dict[str, list[dict]]:
    """
    Paper Agent 메인 실행 함수.
    반환: { group_key: [요약된 paper, ...], ... }
    """
    print("[Paper Agent] arxiv 논문 수집 시작...")
    raw_groups = fetch_all_groups(days_back=days_back)

    summarized: dict[str, list[dict]] = {}
    for group_key, papers in raw_groups.items():
        label = ARXIV_KEYWORD_GROUPS.get(group_key, {}).get("label", group_key)
        print(f"[Paper Agent] '{label}' 논문 {len(papers)}편 요약 중...")
        summarized_papers = []
        for paper in papers:
            print(f"  - {paper['title'][:60]}...")
            summarized_papers.append(summarize_paper(paper))
        summarized[group_key] = summarized_papers

    total = sum(len(v) for v in summarized.values())
    print(f"[Paper Agent] 완료 — 총 {total}편 요약")
    return summarized
