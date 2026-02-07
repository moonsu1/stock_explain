# Vercel 배포 시 백엔드 연결

프론트만 Vercel에 배포한 경우, **백엔드 URL**을 반드시 설정해야 시황 분석·뉴스·포트폴리오 API가 동작합니다.

## 원인

- 로컬: `frontend/.env`에 `VITE_API_URL=http://localhost:8000` 이 있어서 잘 됨.
- Vercel: 환경 변수를 안 넣으면 `VITE_API_URL`이 빈 값이라 요청이 Vercel 도메인(`/api/...`)으로 가서 **Failed to fetch** 발생.

## 해결 방법

1. **백엔드를 먼저 배포**  
   예: Railway에 배포 후 URL 확인 (예: `https://stockexplain-production.up.railway.app`).

2. **Vercel에서 환경 변수 설정**
   - Vercel 대시보드 → 해당 프로젝트 → **Settings** → **Environment Variables**
   - 추가:
     - **Name**: `VITE_API_URL`
     - **Value**: 백엔드 URL (예: `https://stockexplain-production.up.railway.app`)
     - **Environment**: Production, Preview, Development 전부 체크 권장
   - 저장.

3. **재배포**
   - **Deployments** 탭에서 최신 배포 옆 **⋯** → **Redeploy**  
   - 또는 새 커밋 푸시 후 자동 배포.

> `VITE_` 로 시작하는 변수만 빌드 시 프론트 코드에 들어가므로, 이름을 정확히 `VITE_API_URL`로 해야 합니다.

## 확인

재배포 후 시황 분석 페이지에서 "Failed to fetch"가 사라지고, 실시간 분석·뉴스가 로드되면 정상 연결된 것입니다.

---

## 환경 변수는 맞는데 갑자기 안 될 때

- **Vercel URL이 바뀐 경우** (프리뷰 배포, 도메인 변경): 백엔드 CORS가 예전 URL만 허용하면 막힙니다. 백엔드(main.py)에서는 `*.vercel.app` 출처를 자동 허용하므로, **백엔드를 한 번 재배포**(Railway 등)하면 해결됩니다.
- **Railway 무료 플랜**: 일정 시간 미사용 시 슬립합니다. 첫 요청이 30초 안에 안 오면 타임아웃으로 Failed to fetch가 날 수 있으니, 한 번 새로고침해 보세요.
