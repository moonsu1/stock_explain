# 키움증권 주식 투자 시스템

키움증권 REST API(앱키/시크릿)를 활용한 시황 분석 및 자동매매 시스템입니다.

## 주요 기능

- **시황 분석 리포트**: 나스닥, 코스피, 코스닥 지수 실시간 조회 및 분석
- **포트폴리오 관리**: 키움 계좌 연동, 보유 종목 조회, 손익 현황
- **자동매매 시스템**: 전략 기반 자동 주문 실행

## 사전 준비

### 1. 키움증권 REST API 앱키/시크릿
키움증권 REST API 서비스에서 앱키·시크릿을 발급받아 `backend/.env`에 설정합니다.  
상세: **[docs/KIWOOM_SETUP.md](docs/KIWOOM_SETUP.md)**.

### 2. OpenAI API 키 발급
시황 분석 기능을 위해 OpenAI API 키가 필요합니다.  
https://platform.openai.com/api-keys

## 설치 방법

### Backend 설치
```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
# .env에 KIWOOM_APPKEY, KIWOOM_SECRETKEY, OPENAI_API_KEY 등 입력
```

### Frontend 설치
```bash
cd frontend
npm install
```

## 실행 방법

### Backend 실행
```bash
cd backend
python main.py
```

### Frontend 실행
```bash
cd frontend
npm run dev
```

## 프로젝트 구조

```
cursor_money/
├── backend/
│   ├── main.py              # FastAPI 서버
│   ├── kiwoom/
│   │   ├── api.py           # 키움 API 래퍼
│   │   └── trader.py        # 자동매매 로직
│   ├── analysis/
│   │   ├── market.py        # 시황 분석
│   │   └── news.py          # 뉴스 크롤링
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── pages/
│   └── package.json
└── README.md
```

## Vercel 배포 (프론트)

프론트만 Vercel에 올린 경우 **Environment Variables**에 `VITE_API_URL` = 백엔드 URL(예: Railway 주소)을 꼭 넣고 재배포하세요. 안 넣으면 시황 분석·뉴스에서 Failed to fetch 납니다. 자세한 단계: **[docs/VERCEL_DEPLOY.md](docs/VERCEL_DEPLOY.md)**.

## 주의사항

- 키움 연동은 **REST API 앱키/시크릿**으로 하며, OS 제한 없음 (상세는 [docs/KIWOOM_SETUP.md](docs/KIWOOM_SETUP.md))
- **장 운영시간**(09:00~15:30)에만 실시간 데이터 수신 가능
- 자동매매는 반드시 **모의투자**로 먼저 테스트하세요
- API 호출 제한이 있으니 과도한 요청을 피하세요

## 라이선스

MIT License
