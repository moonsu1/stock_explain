"""
중앙 설정 파일 — 키워드 그룹, LLM 설정, 크롤링 대상 등
키워드 추가/수정은 이 파일에서만 하면 됩니다.
"""

# ─────────────────────────────────────────────────────────────
# arxiv 논문 수집 키워드 그룹
# 각 그룹에서 MAX_PAPERS_PER_GROUP 편씩 수집
# ─────────────────────────────────────────────────────────────
ARXIV_KEYWORD_GROUPS = {
    "agent_system": {
        "label": "파트 1 — Agent System / LLM Training",
        "emoji": "🤖",
        "keywords": [
            "LLM agent planning",
            "LLM reasoning agent",
            "agentic AI orchestration",
            "super agent LLM",
            "multi-agent system LLM",
            "LLM pretraining",
            "LLM fine-tuning instruction",
            "RLHF language model",
        ],
        "perspective": (
            "삼성리서치 Agent for Device 팀 파트1(Agent System) 관점에서, "
            "이 논문이 Planning·Reasoning 오케스트레이터 모델 학습(프리트레이닝/파인튜닝)에 "
            "어떻게 기여할 수 있는지 설명해주세요."
        ),
    },
    "web_agent": {
        "label": "파트 2 — Web Agent / GUI Agent",
        "emoji": "🌐",
        "keywords": [
            "web agent browser",
            "GUI agent automation",
            "computer use VLM",
            "screen understanding action",
            "vision language model UI",
            "multimodal agent grounding",
        ],
        "perspective": (
            "삼성리서치 Agent for Device 팀 파트2(Web Agent) 관점에서, "
            "이 논문이 브라우저 조작 에이전트의 VLM 기반 화면 이해·클릭 좌표 계산·Action Policy 개선에 "
            "어떻게 기여할 수 있는지 설명해주세요."
        ),
    },
    "generative_ui": {
        "label": "파트 3 — Generative UI",
        "emoji": "🎨",
        "keywords": [
            "generative UI LLM",
            "dynamic interface generation",
            "UI generation multimodal",
            "adaptive UI AI",
            "code generation UI component",
        ],
        "perspective": (
            "삼성리서치 Agent for Device 팀 파트3(Generative UI) 관점에서, "
            "이 논문이 사용자 의도 기반 실시간 UI 생성 기술에 "
            "어떻게 기여할 수 있는지 설명해주세요."
        ),
    },
    "knowledge_graph": {
        "label": "Knowledge Graph / Ontology",
        "emoji": "🕸️",
        "keywords": [
            "knowledge graph LLM",
            "ontology reasoning LLM",
            "graph RAG retrieval",
            "KG augmented generation",
            "graph neural network reasoning",
        ],
        "perspective": (
            "AI 엔지니어(온톨로지·Knowledge Graph·Multi-agent 전문) 관점에서, "
            "이 논문이 LLM과 Knowledge Graph의 융합, "
            "또는 Graph 기반 RAG/추론 고도화에 어떻게 활용될 수 있는지 설명해주세요."
        ),
    },
}

# 그룹별 수집 논문 수
MAX_PAPERS_PER_GROUP = 3

# ─────────────────────────────────────────────────────────────
# 웹 크롤링 / RSS 설정
# ─────────────────────────────────────────────────────────────
NEWS_SOURCES = {
    "huggingface_papers": "https://huggingface.co/papers",
    "venturebeat_ai": "https://venturebeat.com/category/ai/",
}

GOOGLE_NEWS_RSS_KEYWORDS = [
    "AI agent 2026",
    "LLM fine-tuning 2026",
    "web agent computer use",
    "Cursor AI coding",
    "Claude Code agent",
    "generative UI",
    "knowledge graph LLM",
]

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

# ─────────────────────────────────────────────────────────────
# LLM 설정 (Gemini 기본 / Claude 대안)
# ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-haiku-4-5"

# Gemini 무료 티어 Rate Limit 대응: API 호출 사이 대기 시간(초)
# gemini-2.5-flash 무료 티어: 분당 5회 → 최소 12초 간격 필요
LLM_REQUEST_DELAY_SEC = 13

# ─────────────────────────────────────────────────────────────
# 이메일 설정
# ─────────────────────────────────────────────────────────────
EMAIL_SUBJECT_TEMPLATE = "[AI 브리핑] {date} — 최신 논문 및 AI 트렌드"

# 뉴스 최신성 필터: 오늘 기준 최대 허용 일수
NEWS_MAX_AGE_DAYS = 60
