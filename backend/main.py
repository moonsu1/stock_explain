# -*- coding: utf-8 -*-
"""
키움증권 주식 투자 시스템 - FastAPI 메인 서버
"""
import os
import sys

# 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 환경변수 로드
load_dotenv()

# 라우터 임포트
from api.routes import market, portfolio, trade, analysis

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 컨텍스트 매니저"""
    print("[Server] Starting Kiwoom Investment System...")
    
    # 시작 시 크롤러 테스트
    try:
        from analysis.crawler import get_all_indices
        indices = get_all_indices()
        for idx in indices:
            sign = "+" if idx.change >= 0 else ""
            print(f"  {idx.name}: {idx.value:,.2f} ({sign}{idx.change_percent:.2f}%)")
        print("[OK] Market data crawler working")
    except Exception as e:
        print(f"[Warning] Crawler test failed: {e}")
    
    # OpenAI 연결 확인
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key.startswith("sk-"):
        print("[OK] OpenAI API key configured")
    else:
        print("[Warning] OpenAI API key not set - using mock analysis")
    
    yield
    print("[Server] Shutting down...")

app = FastAPI(
    title="Kiwoom Investment System",
    description="Real-time market analysis and auto-trading API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (allow_credentials=True 시 와일드카드 불가 → 도메인 명시)
_cors_origins = ["http://localhost:3000", "http://localhost:5173"]
_frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip()
if _frontend_origin:
    _cors_origins.extend([o.strip() for o in _frontend_origin.split(",") if o.strip()])
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(trade.router, prefix="/api/trade", tags=["Trade"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])

@app.get("/")
async def root():
    return {
        "message": "Kiwoom Investment System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"\n[Server] Running on http://{host}:{port}")
    print(f"[Server] API docs: http://localhost:{port}/docs\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
