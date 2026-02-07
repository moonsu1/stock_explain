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

### 카톡/인앱·모바일에서 접속할 때 (BACKEND_URL)

브라우저에서는 되는데 **카톡으로 링크 열면** 또는 **모바일에서** Network Error가 나는 경우, 같은 오리진 프록시를 써야 합니다.

- **해결**: Vercel 환경 변수에 **`BACKEND_URL`**을 넣어 주세요. (값 = 밖에서 접속 가능한 백엔드 주소)
- 그러면 API 요청이 `xxx.vercel.app/api/proxy/...` 로 가고, Vercel 서버가 **BACKEND_URL**로 대신 요청해서 응답을 돌려줍니다.
- **BACKEND_URL** 예:
  - Railway 배포: `https://xxx.up.railway.app`
  - **로컬 백엔드 + ngrok**: ngrok 실행 후 나오는 `https://xxxx.ngrok-free.app` → 자세한 순서는 **[docs/NGROK.md](NGROK.md)** 참고.

## 확인

재배포 후 시황 분석 페이지에서 "Failed to fetch"가 사라지고, 실시간 분석·뉴스가 로드되면 정상 연결된 것입니다.

---

## 405 / 304 / 대시보드·포트폴리오가 비어 있을 때

- **405 Method Not Allowed**: 키움 연동·구조화 분석 버튼에서 405가 나오면, **백엔드가 해당 URL에서 POST를 받지 못하는 상태**입니다.  
  1. **Vercel**에서 `BACKEND_URL`이 **실제 백엔드 주소**(Railway 등)와 **완전히 동일**한지 확인하세요. 끝에 `/` 없이, `https://...` 형태로.  
  2. **Railway(또는 사용 중인 백엔드)**에서 서비스가 **실행 중**인지, 로그에 에러가 없는지 확인하세요.  
  3. BACKEND_URL을 잘못된 주소(정적 사이트, 다른 서비스)로 두면 POST 요청이 405를 반환할 수 있습니다.

- **304 Not Modified**: API가 304를 주면 브라우저가 **캐시된 응답**을 씁니다. 프론트에서는 API 요청에 캐시 방지 헤더를 넣어 두었으므로, 백엔드가 정상 응답(200)을 주면 데이터가 채워져야 합니다. 계속 304만 나오고 데이터가 비어 있으면, 백엔드 URL/동작을 먼저 확인하세요.

- **대시보드·포트폴리오가 0원/빈 목록**: 위처럼 백엔드가 연결되지 않았거나 405·에러로 실패하면, 프론트는 빈 배열·0으로 보여줍니다. **백엔드 연결이 정상**이면 실제 데이터가 표시됩니다.

---

## 환경 변수는 맞는데 갑자기 안 될 때

- **Vercel URL이 바뀐 경우** (프리뷰 배포, 도메인 변경): 백엔드 CORS가 예전 URL만 허용하면 막힙니다. 백엔드(main.py)에서는 `*.vercel.app` 출처를 자동 허용하므로, **백엔드를 한 번 재배포**(Railway 등)하면 해결됩니다.
- **Railway 무료 플랜**: 일정 시간 미사용 시 슬립합니다. 첫 요청이 30초 안에 안 오면 타임아웃으로 Failed to fetch가 날 수 있으니, 한 번 새로고침해 보세요.
