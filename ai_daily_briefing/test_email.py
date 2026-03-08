import sys
sys.stdout.reconfigure(encoding='utf-8')
from tools.email_tool import build_html_email, send_email

# 더미 데이터로 이메일 발송 테스트
dummy_paper_sections = {
    "agent_system": [
        {
            "id": "test001",
            "title": "[테스트] LLM Agent Planning Survey 2026",
            "authors": ["Kim Moon-su", "Test Author"],
            "url": "https://arxiv.org/abs/test001",
            "published": "2026-03-08",
            "abstract": "이것은 테스트용 초록입니다.",
            "gemini_summary": "**핵심 기여**: 테스트 논문입니다.\n**팀 활용 포인트**: 이메일 발송 테스트용입니다.\n**한계**: 없음",
            "group_key": "agent_system",
            "group_label": "파트 1 — Agent System / LLM Training",
            "group_emoji": "🤖",
        }
    ],
    "web_agent": [],
    "generative_ui": [],
    "knowledge_graph": [],
}

dummy_news = [
    {
        "source": "테스트",
        "title": "AI Daily Briefing 이메일 발송 테스트",
        "url": "https://example.com",
        "gemini_summary": "이것은 이메일 발송 테스트용 동향 요약입니다. 실제 실행 시 Gemini가 생성합니다.",
    }
]

html = build_html_email(dummy_paper_sections, dummy_news, "2026년 03월 08일 (테스트)")
result = send_email(html, "[테스트] AI Daily Briefing 이메일 발송 확인")

if result:
    print("PASS: 이메일 발송 성공!")
else:
    print("FAIL: 이메일 발송 실패")
