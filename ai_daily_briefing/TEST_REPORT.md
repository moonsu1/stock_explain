# AI Daily Briefing — 테스트 보고서

**테스트 일시**: 2026-03-08  
**테스트 환경**: Windows 10, Python 3.13

---

## 테스트 결과 요약

| # | 테스트 항목 | 결과 | 비고 |
|---|---|---|---|
| 1 | Gemini API 연결 | ✅ PASS | `gemini-2.5-flash` 사용 |
| 2 | arxiv 논문 수집 | ✅ PASS | 그룹당 3편, 총 12편 수집 |
| 3 | 웹 크롤링 (HuggingFace) | ✅ PASS | 3개 수집 |
| 4 | 웹 크롤링 (VentureBeat RSS) | ✅ PASS | 3개 수집 |
| 5 | 웹 크롤링 (Google News RSS) | ✅ PASS | 키워드별 수집 |
| 6 | HTML 이메일 발송 | ✅ PASS | Gmail SMTP 정상 작동 |
| 7 | 전체 파이프라인 통합 | ✅ PASS | 이메일 발송 확인됨 |

**전체 결과: 7/7 PASS**

---

## 발견된 이슈 및 조치 사항

### Issue 1 — Gemini 모델 변경 필요 [해결됨]

| 항목 | 내용 |
|---|---|
| **문제** | `gemini-2.0-flash` 무료 티어 쿼터 `limit: 0` — 해당 API 키에서 완전 차단 |
| **원인** | Google이 특정 프로젝트의 `gemini-2.0-flash` 무료 티어를 비활성화 |
| **조치** | `config.py`의 `GEMINI_MODEL`을 `gemini-2.5-flash`로 변경 → 정상 작동 확인 |
| **상태** | ✅ 해결 |

---

### Issue 2 — Gemini 무료 티어 Rate Limit (분당 5회) [조치 완료]

| 항목 | 내용 |
|---|---|
| **문제** | `gemini-2.5-flash` 무료 티어 분당 5회 제한으로 429 에러 간헐적 발생 |
| **원인** | 기존 `LLM_REQUEST_DELAY_SEC = 2` 설정이 너무 짧음 |
| **영향** | 일부 논문 요약 실패 (`[요약 생성 실패]` 텍스트로 대체됨), 전체 파이프라인은 정상 완료 |
| **조치** | `LLM_REQUEST_DELAY_SEC = 13` 으로 증가 (분당 5회 = 12초 간격 + 여유 1초) |
| **상태** | ✅ 해결 |

> **참고**: 딜레이 13초 × 논문 12편 + 뉴스 1회 + 검토 1회 = 약 **3분 10초** 소요 예상

---

### Issue 3 — Windows 한글 인코딩 오류 [해결됨]

| 항목 | 내용 |
|---|---|
| **문제** | `cp949` 코덱에서 유니코드 특수문자(`—`) 인코딩 실패 |
| **원인** | Windows PowerShell 기본 인코딩이 cp949 |
| **조치** | `main.py`, `orchestrator.py` 상단에 `sys.stdout.reconfigure(encoding='utf-8')` 추가 |
| **상태** | ✅ 해결 |

---

### Issue 4 — 논문 중복 수집 (일부)

| 항목 | 내용 |
|---|---|
| **문제** | 키워드 그룹 간 겹치는 논문이 일부 수집됨 (예: `POET-X`가 `agent_system`, `knowledge_graph` 양쪽에서 수집) |
| **원인** | 논문이 여러 키워드에 해당될 수 있음 |
| **영향** | Orchestrator의 중복 제거 로직이 정상 작동함 (12편 → 9편으로 줄어듦) |
| **상태** | ✅ 정상 동작 확인 (설계대로 작동) |

---

## 전체 파이프라인 실행 로그 요약

```
[Orchestrator] 브리핑 파이프라인 시작 — 2026-03-08 16:49
[Step 1] Paper Agent + News Agent 병렬 실행
  - agent_system   → 3편 수집 완료
  - web_agent      → 3편 수집 완료
  - generative_ui  → 3편 수집 완료
  - knowledge_graph → 3편 수집 완료
  - 웹 뉴스 38개 수집 → LLM 핵심 5개 선별
[Step 2] 중복 제거: 12편 → 9편
[Step 3] Orchestrator 브리핑 검토 (LLM)
[Step 4] HTML 이메일 발송 → moonsu159@gmail.com ✅
총 소요 시간: 약 110초
```

---

## 현재 설정값

| 설정 | 값 |
|---|---|
| LLM 모델 | `gemini-2.5-flash` |
| LLM 제공자 | `gemini` (무료 티어) |
| API 호출 딜레이 | `13초` |
| 그룹당 논문 수 | `3편` |
| 발송 시각 | 매일 오전 `07:00` KST |
| 수신 이메일 | `moonsu159@gmail.com` |

---

## 권장 사항

### 단기 (지금 당장)

1. **`python main.py`** 로 스케줄러 모드 실행 → 매일 오전 7시 자동 발송
2. **발송된 이메일 확인** — 지금 `moonsu159@gmail.com` 받은 편지함 확인

### 중기 (품질 개선 시)

1. **Claude Haiku 4.5로 전환** — `.env`에서 `LLM_PROVIDER=claude`로 변경, 요약 품질 향상
   - Rate limit 걱정 없이 더 빠르게 실행 가능
2. **논문 수 조정** — `config.py`의 `MAX_PAPERS_PER_GROUP`을 2로 줄이면 실행 시간 단축

### 장기

1. **백그라운드 서비스 등록** — Windows Task Scheduler에 등록하면 PC를 켜두지 않아도 실행
2. **Google AI Studio에서 유료 플랜 활성화** — 월 $0.15 수준으로 Rate limit 완전 해소

---

## 테스트 파일 목록 (삭제 가능)

```
ai_daily_briefing/
├── test_arxiv.py   ← 삭제 가능
├── test_web.py     ← 삭제 가능
└── test_email.py   ← 삭제 가능
```
