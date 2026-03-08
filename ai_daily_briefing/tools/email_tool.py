"""
이메일 발송 툴
- smtplib + Gmail App Password 방식
- 섹션별 컬러 구분이 적용된 HTML 이메일
"""

import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def _md_to_html(text: str) -> str:
    """마크다운 기본 문법을 HTML로 변환합니다."""
    # ### 제목 제거 (섹션 타이틀 역할이므로 단순 굵게 처리)
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<strong>\1</strong>", text, flags=re.MULTILINE)
    # **굵게**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # *기울임*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # 줄바꿈 → <br>
    text = text.replace("\n", "<br>")
    # --- 구분선 제거
    text = re.sub(r"<br>-{3,}<br>", "<br>", text)
    return text


# 섹션 키별 컬러 테마
SECTION_COLORS = {
    "agent_system":    "#4A90E2",   # 블루
    "web_agent":       "#27AE60",   # 그린
    "generative_ui":   "#9B59B6",   # 퍼플
    "knowledge_graph": "#E67E22",   # 오렌지
    "news_trends":     "#E74C3C",   # 레드
}

SECTION_BG_COLORS = {
    "agent_system":    "#EBF5FB",
    "web_agent":       "#EAFAF1",
    "generative_ui":   "#F5EEF8",
    "knowledge_graph": "#FEF9E7",
    "news_trends":     "#FDEDEC",
}


def _build_paper_section_html(group_key: str, group_label: str, emoji: str, papers: list[dict]) -> str:
    color = SECTION_COLORS.get(group_key, "#555555")
    bg = SECTION_BG_COLORS.get(group_key, "#F9F9F9")

    if not papers:
        paper_html = "<p style='color:#999; font-style:italic;'>오늘 해당 논문 없음</p>"
    else:
        items = []
        for i, p in enumerate(papers, 1):
            authors = ", ".join(p.get("authors", []))
            raw_summary = p.get("gemini_summary", "")
            # 요약 생성 실패 시 — 초록 원문 노출 대신 안내 메시지로 대체
            if not raw_summary or raw_summary.startswith("[요약 생성"):
                raw_summary = (
                    "⚠️ 오늘 AI 요약을 불러오지 못했습니다. "
                    "논문 제목을 클릭하면 arxiv 원문에서 직접 확인하실 수 있습니다."
                )
            summary = _md_to_html(raw_summary)
            items.append(f"""
            <div style='margin-bottom:16px; padding:12px; background:#fff; border-left:4px solid {color}; border-radius:4px;'>
                <p style='margin:0 0 4px 0; font-size:15px; font-weight:bold;'>
                    {i}. <a href='{p["url"]}' style='color:{color}; text-decoration:none;'>{p["title"]}</a>
                </p>
                <p style='margin:0 0 6px 0; font-size:12px; color:#777;'>
                    {authors} &nbsp;|&nbsp; {p.get("published", "")}
                </p>
                <div style='margin:0; font-size:13px; color:#333; line-height:1.8;'>{summary}</div>
            </div>
            """)
        paper_html = "".join(items)

    return f"""
    <div style='margin-bottom:32px; padding:16px; background:{bg}; border-radius:8px;'>
        <h2 style='margin:0 0 12px 0; color:{color}; font-size:17px; border-bottom:2px solid {color}; padding-bottom:6px;'>
            {emoji} {group_label}
        </h2>
        {paper_html}
    </div>
    """


def _build_news_section_html(news_items: list[dict]) -> str:
    color = SECTION_COLORS["news_trends"]
    bg = SECTION_BG_COLORS["news_trends"]

    if not news_items:
        content = "<p style='color:#999; font-style:italic;'>오늘 수집된 동향 없음</p>"
    else:
        rows = []
        for i, item in enumerate(news_items, 1):
            raw_summary = item.get("gemini_summary", "")
            summary_html = _md_to_html(raw_summary) if raw_summary else ""
            title = item.get("title", "")
            url = item.get("url", "") or "#"
            source = item.get("source", "")

            title_tag = (
                f"<a href='{url}' style='color:{color}; text-decoration:none;'>{title}</a>"
                if url != "#" else title
            )
            published = item.get("published", "")
            # RSS 날짜 → 간결한 형식으로 변환 (예: 2026-03-01)
            pub_display = ""
            if published:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(published)
                    pub_display = pub_dt.strftime("%Y-%m-%d")
                except Exception:
                    pub_display = published[:16]
            meta = f"{source}" + (f" &nbsp;|&nbsp; {pub_display}" if pub_display else "")
            rows.append(f"""
            <div style='margin-bottom:16px; padding:12px; background:#fff; border-left:4px solid {color}; border-radius:4px;'>
                <p style='margin:0 0 4px 0; font-size:15px; font-weight:bold;'>
                    {i}. {title_tag}
                </p>
                <p style='margin:0 0 8px 0; font-size:11px; color:#999;'>{meta}</p>
                <div style='font-size:13px; color:#333; line-height:1.8;'>{summary_html}</div>
            </div>
            """)
        content = "".join(rows)

    return f"""
    <div style='margin-bottom:32px; padding:16px; background:{bg}; border-radius:8px;'>
        <h2 style='margin:0 0 12px 0; color:{color}; font-size:17px; border-bottom:2px solid {color}; padding-bottom:6px;'>
            📰 오늘의 AI 신기술 동향 (TOP 5)
        </h2>
        {content}
    </div>
    """


def build_html_email(
    paper_sections: dict,
    news_items: list[dict],
    date_str: str,
) -> str:
    """전체 HTML 이메일 본문을 생성합니다."""
    sections_html = ""
    for group_key, papers in paper_sections.items():
        from config import ARXIV_KEYWORD_GROUPS
        group = ARXIV_KEYWORD_GROUPS.get(group_key, {})
        sections_html += _build_paper_section_html(
            group_key=group_key,
            group_label=group.get("label", group_key),
            emoji=group.get("emoji", "📄"),
            papers=papers,
        )

    sections_html += _build_news_section_html(news_items)

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:#F4F6F8; margin:0; padding:20px;'>
        <div style='max-width:700px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);'>

            <!-- 헤더 -->
            <div style='background:linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding:28px 24px; text-align:center;'>
                <h1 style='margin:0; color:#fff; font-size:22px; font-weight:700;'>🤖 AI Daily Briefing</h1>
                <p style='margin:8px 0 0 0; color:#a0b4cc; font-size:14px;'>
                    {date_str} &nbsp;|&nbsp; 최신 논문 및 AI 트렌드
                </p>
            </div>

            <!-- 본문 -->
            <div style='padding:24px;'>
                {sections_html}
            </div>

            <!-- 푸터 -->
            <div style='padding:16px 24px; background:#F8F9FA; text-align:center; border-top:1px solid #E9ECEF;'>
                <p style='margin:0; font-size:12px; color:#888;'>
                    AI Daily Briefing &nbsp;|&nbsp; 자동 발송 시스템
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def send_email(html_body: str, subject: str) -> bool:
    """Gmail SMTP를 통해 HTML 이메일을 발송합니다."""
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        print("  [email] .env에 EMAIL_SENDER / EMAIL_PASSWORD / EMAIL_RECEIVER가 설정되지 않았습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"  [email] 발송 완료 → {receiver}")
        return True
    except Exception as e:
        print(f"  [email] 발송 실패: {e}")
        return False
