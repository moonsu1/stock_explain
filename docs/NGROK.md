# ngrok으로 로컬 백엔드 열기 (모바일/외부에서 접속)

PC에서만 돌리는 백엔드를 **ngrok**으로 인터넷에 잠깐 열어두면, Vercel 프론트(모바일 포함)에서 그 주소로 접속할 수 있어.

---

## 1. ngrok 설치

**방법 A – 공식 사이트**  
- https://ngrok.com 가서 가입 후 다운로드  
- Windows면 `ngrok.exe` 받아서 PATH 넣거나, 사용할 폴더에 둠

**방법 B – npm (이미 Node 있으면)**  
```bash
npm install -g ngrok
```

**방법 C – 한 번만 쓸 때**  
```bash
npx ngrok http 8000
```
(매번 이렇게 실행해도 됨)

---

## 2. 백엔드 실행

터미널에서 백엔드를 **8000번 포트**로 실행해 둬.

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` 이어야 ngrok이 접속받을 수 있어.

---

## 3. ngrok 터널 켜기

**새 터미널** 하나 더 열고:

```bash
ngrok http 8000
```

또는 npm으로 설치했으면:

```bash
npx ngrok http 8000
```

실행하면 예시처럼 나와:

```
Forwarding    https://abcd-12-34-56-78.ngrok-free.app -> http://localhost:8000
```

여기 나오는 **https://xxxx.ngrok-free.app** 주소가 “밖에서 보는 백엔드 주소”야.  
이 주소를 복사해 둬.

> 무료 플랜은 ngrok 켤 때마다 주소가 바뀌어. 바꿀 때마다 Vercel `BACKEND_URL`도 같이 바꿔줘야 해.

---

## 4. Vercel에 BACKEND_URL 설정

1. **Vercel** 대시보드 → 해당 프로젝트 → **Settings** → **Environment Variables**
2. **`BACKEND_URL`** 찾아서 수정(또는 새로 추가)
   - **Value**: ngrok에서 복사한 주소 그대로 (끝에 `/` 없이)  
     예: `https://abcd-12-34-56-78.ngrok-free.app`
3. **Save** 후, **Deployments** → 최신 배포 **Redeploy** 한 번 해줘.

---

## 5. 사용 방법

1. **백엔드** 켜 둔 상태 (8000 포트)
2. **ngrok** 켜 둔 상태 (`ngrok http 8000`)
3. **모바일**에서 Vercel 앱 주소로 접속

모바일은 `/api/proxy`로 요청하고, Vercel이 `BACKEND_URL`(ngrok 주소)로 넘겨줘서 네 PC 백엔드까지 연결돼.

---

## 주의사항

- **ngrok 끄면** 그 주소로 접속 안 됨. 모바일 쓸 때만 ngrok 켜 두면 됨.
- **ngrok 다시 켜면** 주소가 바뀌므로, **Vercel `BACKEND_URL`**을 새 주소로 바꾸고 **Redeploy** 해야 해.
- ngrok 무료는 가끔 브라우저에 “Visit Site” 버튼 나오는 페이지를 먼저 띄울 수 있음. 그건 브라우저에서 한 번 넘기면 되고, **Vercel 프록시**가 보내는 요청은 보통 그냥 통과해.

끝.
