# AI Daily Briefing

매일 아침 arxiv 최신 논문 요약 + AI 기술 동향을 이메일로 자동 발송하는 시스템입니다.
**삼성리서치 Agent for Device 팀** 3개 파트 관점으로 특화되어 있습니다.

## 이메일 섹션 구성

| 섹션 | 내용 |
|---|---|
| 🤖 파트 1 — Agent System / LLM Training | Planning·Reasoning·Pretraining·Fine-tuning 논문 |
| 🌐 파트 2 — Web Agent / GUI Agent | VLM, Computer Use, Screen Understanding 논문 |
| 🎨 파트 3 — Generative UI | Dynamic Interface, Multimodal UI 논문 |
| 🕸️ Knowledge Graph / Ontology | KG+LLM 융합, Graph RAG 논문 |
| 📰 AI 신기술 동향 | HuggingFace, VentureBeat, Google News 기반 |

---

## 빠른 시작

### 1. 의존성 설치

```bash
cd ai_daily_briefing
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 복사해서 `.env`를 만들고 값을 채워주세요:

```bash
copy .env.example .env
```

| 변수 | 설명 |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급 (무료) |
| `ANTHROPIC_API_KEY` | Claude 사용 시 설정 (선택) |
| `LLM_PROVIDER` | `gemini` (기본) 또는 `claude` |
| `EMAIL_SENDER` | Gmail 주소 |
| `EMAIL_PASSWORD` | Gmail **앱 비밀번호** (일반 비밀번호 X) |
| `EMAIL_RECEIVER` | 수신 이메일 주소 |

### Gmail 앱 비밀번호 발급 방법

1. Google 계정 → **보안** → **2단계 인증** 활성화
2. 보안 → **앱 비밀번호** → 앱: 메일, 기기: Windows 컴퓨터
3. 생성된 16자리 비밀번호를 `EMAIL_PASSWORD`에 입력

### 3. 즉시 테스트 실행

```bash
python main.py --now
```

### 4. 스케줄러 모드 (매일 오전 7시 자동 실행)

```bash
python main.py
```

---

## 키워드 추가/수정

`config.py`의 `ARXIV_KEYWORD_GROUPS`에서 그룹별 키워드를 자유롭게 수정할 수 있습니다.

```python
ARXIV_KEYWORD_GROUPS = {
    "agent_system": {
        "keywords": ["LLM agent planning", "새로운 키워드 추가", ...],
        ...
    },
    ...
}
```

## LLM 모델 교체

`.env`에서 한 줄만 변경하면 됩니다:

```env
# Gemini 사용 (무료 티어, 기본값)
LLM_PROVIDER=gemini

# Claude Haiku 4.5로 교체 (더 높은 품질)
LLM_PROVIDER=claude
```

---

## 비용 안내

| 모델 | 무료 한도 | 유료 전환 시 월 비용 (예상) |
|---|---|---|
| Gemini 2.0 Flash | 250 req/일 (이 시스템에 충분) | ~$0.15 |
| Claude Haiku 4.5 | $5 초기 크레딧 | ~$3.00 |

---

## 프로젝트 구조

```
ai_daily_briefing/
├── main.py              # 진입점 + APScheduler
├── config.py            # 키워드 그룹, 설정 중앙화
├── requirements.txt
├── .env                 # API 키, 이메일 설정 (git 제외)
├── agents/
│   ├── llm_client.py    # LLM 추상화 (Gemini/Claude 교체 가능)
│   ├── orchestrator.py  # PM Agent: 전체 흐름 조율
│   ├── paper_agent.py   # arxiv 논문 수집 + 요약
│   └── news_agent.py    # 웹 크롤링 기술 동향
├── tools/
│   ├── arxiv_tool.py    # arxiv 라이브러리 래퍼
│   ├── web_search_tool.py # HuggingFace, VentureBeat, Google News
│   └── email_tool.py    # HTML 이메일 발송
└── prompts/
    └── templates.py     # LLM 프롬프트 템플릿
```
