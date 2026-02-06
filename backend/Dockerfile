# Backend API - Python 3.11 (runtime.txt 기준)
FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 복사 후 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사 (.env는 제외, 실행 시 env_file로 주입)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
