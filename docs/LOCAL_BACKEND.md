# 로컬 백엔드 실행 (Docker)

Railway egress IP가 주기적으로 바뀌어 키움 개발자센터 IP 등록을 유지하기 어려운 경우, 백엔드를 로컬에서 Docker로 상시 실행해 사용할 수 있습니다.

## 사전 준비

1. **backend/.env**  
   `backend/.env.example`을 참고해 `backend/.env`를 만들고 다음을 설정합니다.
   - `OPENAI_API_KEY=sk-...` — AI 시황 분석에 **필수**
   - 키움 API 사용 시: `KIWOOM_APPKEY`, `KIWOOM_SECRETKEY` 등

2. **Docker**  
   Docker Desktop(또는 Docker Engine)이 설치되어 있어야 합니다.

## 백엔드 실행

프로젝트 루트에서:

```bash
docker compose up -d
```

- 백엔드가 포트 **8000**에서 실행됩니다.
- `restart: unless-stopped`로 설정되어 있어, 재부팅 후에도 컨테이너가 자동으로 다시 올라옵니다.
- 중지: `docker compose down`

## 프론트엔드 연동 (Vercel 배포)

프론트는 로컬이 아니라 **Vercel** 등에 배포한다고 가정합니다.

1. **Vercel 환경 변수**  
   Vercel 대시보드 → 프로젝트 → Settings → Environment Variables에서:
   - `VITE_API_URL` = `http://localhost:8000`  
   - (본인 PC에서만 쓸 때: 브라우저가 백엔드 호출 시 자기 PC의 로컬 백엔드를 쓰려면 이렇게 설정. 다른 기기에서는 해당 기기 기준 localhost라서 백엔드에 연결되지 않음.)  
   - 또는 로컬 백엔드를 ngrok 등으로 공개한 URL을 쓸 수 있음.

2. **백엔드 CORS**  
   Vercel에 배포된 프론트 도메인을 백엔드에서 허용해야 합니다.  
   `backend/.env`에 추가:
   ```bash
   FRONTEND_ORIGIN=https://your-app.vercel.app
   ```
   (실제 Vercel 프로젝트 URL로 바꿀 것. 여러 개면 쉼표로 구분.)

3. 배포 후 브라우저에서 Vercel URL로 접속하면, API 요청이 `VITE_API_URL`에 설정한 백엔드(로컬 8000 또는 공개 URL)로 전달됩니다.

## 요약

| 단계 | 명령/설정 |
|------|-----------|
| 백엔드 .env | `OPENAI_API_KEY`, `FRONTEND_ORIGIN=https://xxx.vercel.app` 등 |
| 백엔드 실행 | `docker compose up -d` |
| Vercel env | `VITE_API_URL=http://localhost:8000` (또는 공개 백엔드 URL) |
| 프론트 | Vercel에서 배포 (별도 로컬 실행 없음) |

AI 실시간/구조화 분석이 동작하려면 `OPENAI_API_KEY`가 반드시 설정되어 있어야 합니다.
