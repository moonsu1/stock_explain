# 키움증권 연동 설정

포트폴리오 "키움증권 연동하기"를 **실제 계좌**로 쓰려면 키움 REST API 앱키/시크릿만 설정하면 돼요.  
([Lay4U/KiwoomRestApi](https://github.com/Lay4U/KiwoomRestApi) 기반, OS 제한 없음.)

---

## 1. 필요한 것

| 항목 | 설명 |
|------|------|
| **키움 REST API 앱키/시크릿** | 키움증권 개발자센터(또는 REST API 신청)에서 발급 |
| **Python 패키지** | `pip install -r requirements.txt` 시 `kiwoom-openapi`(Git 설치 포함) 설치됨 |

---

## 2. 환경 변수 (백엔드)

`backend/.env`에 다음을 넣어요.

```env
# 키움증권 REST API (필수)
KIWOOM_APPKEY=발급받은_앱키
KIWOOM_SECRETKEY=발급받은_비밀키

# 계좌 선택 (복수 계좌 시 지정, 없으면 첫 계좌 사용)
KIWOOM_ACCOUNT_NO=64969257-10
```

- **KIWOOM_APPKEY / KIWOOM_SECRETKEY**: 필수. 없으면 모의 데이터로 동작.
- **KIWOOM_ACCOUNT_NO**: 선택. 비워두면 로그인 후 첫 계좌 사용.

---

## 3. 동작 방식 요약

- **앱키·시크릿 설정됨 + kiwoom-openapi 설치됨**  
  → 포트폴리오에서 "키움증권 연동하기" 누르면 REST API로 **실제 계좌/보유종목** 조회 시도.  
- **앱키·시크릿 없음 또는 라이브러리 미설치**  
  → 백엔드가 **모의 데이터** 반환. 프론트는 그대로 표시하고 "내 계정으로 저장" 가능.

직접 입력한 값은 `portfolio_manual`(localStorage)에 저장되므로, 키움 없이도 대시보드·포트폴리오에서 "내 계좌"처럼 쓸 수 있어요.

---

## 4. IP 등록 (배포 시 필수)

키움 API는 **요청이 나가는 IP**를 화이트리스트로 등록해야 해요.  
로컬에서는 “현재 나의 IP”만 등록하면 되지만, **Railway 등에 배포했으면 배포 서버가 나가는 IP**를 따로 등록해야 해요.

- **등록할 IP 확인**: 배포된 백엔드에서  
  **`GET https://<백엔드-URL>/api/portfolio/egress-ip`**  
  호출하면 `ip` 값이 그 서버의 나가는(egress) IP예요. 그 IP를 키움 개발자센터 **IP 등록 및 현황**에 추가하면 됨.
- Railway는 재시작 시 IP가 바뀔 수 있어서, 8005가 다시 나오면 egress-ip 다시 찍어서 바뀐 IP 추가하면 됨.

---

## 5. 오류 대응

| 로그/메시지 | 의미 | 조치 |
|-------------|------|------|
| **8005 / Token이 유효하지 않습니다** | 인증 토큰 만료 또는 앱키/시크릿 오류 | Railway 등에서 **`KIWOOM_APPKEY`**·**`KIWOOM_SECRETKEY`** 또는 **`KIWOOM_API_KEY`**·**`KIWOOM_API_SECRET`** 또는 **`kiwoom_appkey`**·**`kiwoom_secretkey`** 중 하나로 설정. 공백·줄바꿈 없이 붙여넣기. 재연결 후 1회 자동 재시도함. |

---

## 6. 참고

- 키움 REST API·앱키 발급: 키움증권 개발자센터 또는 [키움증권 공식 안내](https://www.kiwoom.com) 참고.
- Python 클라이언트: [Lay4U/KiwoomRestApi](https://github.com/Lay4U/KiwoomRestApi).

| 역할 | 파일 |
|------|------|
| 키움 연결/계좌/보유종목 | `backend/kiwoom/api.py` |
| API 라우트 (connect, account, stocks, summary) | `backend/api/routes/portfolio.py` |
| 환경 변수 예시 | `backend/.env.example` |
| 진단용 (실제/모의 구분) | `GET /api/portfolio/kiwoom-test` |
