# -*- coding: utf-8 -*-
"""
키움증권 주식 투자 시스템 - FastAPI 메인 서버
"""
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uvicorn

load_dotenv()

from api.routes import market, portfolio, trade, analysis

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] Starting Kiwoom Investment System...")
    try:
        from analysis.crawler import get_all_indices
        indices = get_all_indices()
        for idx in indices[:3]:
            sign = "+" if idx.change >= 0 else ""
            print(f"  {idx.name}: {idx.value:,.2f} ({sign}{idx.change_percent:.2f}%)")
        print("[OK] Market data crawler working")
    except Exception as e:
        print(f"[Warning] Crawler test failed: {e}")
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
    lifespan=lifespan,
)

class OptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return Response(status_code=200, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "86400",
            })
        return await call_next(request)

_frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip()
if _frontend_origin:
    _cors_origins = [
        "http://localhost:3000", "http://localhost:5173", "http://localhost:5174",
        "http://localhost:5175", "http://localhost:5176",
    ] + [o.strip() for o in _frontend_origin.split(",") if o.strip()]
    _cors_credentials = True
else:
    _cors_origins = ["*"]
    _cors_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(OptionsMiddleware)

app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(trade.router, prefix="/api/trade", tags=["Trade"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])

@app.get("/")
async def root():
    return {"message": "Kiwoom Investment System API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "backend", "version": "1.0.0"}

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    print(f"\n[Server] Running on http://{host}:{port}")
    print(f"[Server] API docs: http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host=host, port=port, reload=debug)
