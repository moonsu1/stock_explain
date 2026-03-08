"""
[PM 역할] Orchestrator Agent
- Paper Agent + News Agent를 조율합니다
- 중복 논문 제거 및 최종 브리핑 조립을 담당합니다
- 전체 파이프라인의 의사결정자입니다
"""

import sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import agents.paper_agent as paper_agent
import agents.news_agent as news_agent
from agents.llm_client import call_llm
from tools.email_tool import build_html_email, send_email
from prompts.templates import FINAL_BRIEFING_REVIEW_SYSTEM, FINAL_BRIEFING_REVIEW_USER_TEMPLATE
from config import ARXIV_KEYWORD_GROUPS, EMAIL_SUBJECT_TEMPLATE


def _deduplicate_papers(paper_sections: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """전체 섹션에서 중복 arxiv ID를 제거합니다 (먼저 나온 섹션 우선)."""
    seen_ids: set[str] = set()
    deduplicated: dict[str, list[dict]] = {}

    for group_key, papers in paper_sections.items():
        clean = []
        for p in papers:
            pid = p.get("id", "")
            if pid not in seen_ids:
                seen_ids.add(pid)
                clean.append(p)
        deduplicated[group_key] = clean

    return deduplicated


def _build_briefing_summary(paper_sections: dict, news_items: list[dict]) -> str:
    """Orchestrator 검토용 브리핑 요약 텍스트를 생성합니다."""
    lines = []
    for group_key, papers in paper_sections.items():
        label = ARXIV_KEYWORD_GROUPS.get(group_key, {}).get("label", group_key)
        lines.append(f"\n[{label}]")
        for p in papers:
            lines.append(f"  - [{p.get('id','')}] {p['title']}")
    lines.append("\n[AI 동향]")
    for item in news_items[:3]:
        lines.append(f"  - {item.get('title', '')}")
    return "\n".join(lines)


def run_briefing(days_back: int = 3) -> bool:
    """
    전체 브리핑 파이프라인을 실행합니다.
    1. Paper Agent → News Agent 순차 실행 (Rate Limit 충돌 방지)
    2. 중복 제거
    3. Orchestrator 검토 (LLM)
    4. HTML 이메일 생성 및 발송
    """
    print("=" * 60)
    print(f"[Orchestrator] 브리핑 파이프라인 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 1: Paper Agent → News Agent 순차 실행
    print("\n[Orchestrator] Step 1-A: Paper Agent 실행")
    paper_sections = paper_agent.run(days_back=days_back)

    print("\n[Orchestrator] Step 1-B: News Agent 실행")
    news_items = news_agent.run()

    # Step 2: 중복 논문 제거
    print("\n[Orchestrator] Step 2: 중복 논문 제거")
    paper_sections = _deduplicate_papers(paper_sections)
    total_papers = sum(len(v) for v in paper_sections.values())
    print(f"  → 최종 논문 수: {total_papers}편")

    # Step 3: Orchestrator 검토 (LLM)
    print("\n[Orchestrator] Step 3: 브리핑 검토 (LLM)")
    briefing_summary = _build_briefing_summary(paper_sections, news_items)
    review = call_llm(
        system_prompt=FINAL_BRIEFING_REVIEW_SYSTEM,
        user_prompt=FINAL_BRIEFING_REVIEW_USER_TEMPLATE.format(
            briefing_summary=briefing_summary
        ),
    )
    print(f"  → 검토 완료:\n{review[:300]}...")

    # Step 4: HTML 이메일 생성 및 발송
    print("\n[Orchestrator] Step 4: 이메일 생성 및 발송")
    date_str = datetime.now().strftime("%Y년 %m월 %d일")
    html_body = build_html_email(
        paper_sections=paper_sections,
        news_items=news_items,
        date_str=date_str,
    )

    subject = EMAIL_SUBJECT_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d")
    )
    success = send_email(html_body=html_body, subject=subject)

    print("\n" + "=" * 60)
    if success:
        print("[Orchestrator] 브리핑 파이프라인 완료!")
    else:
        print("[Orchestrator] 이메일 발송 실패 — .env 설정을 확인해주세요.")
    print("=" * 60)

    return success
