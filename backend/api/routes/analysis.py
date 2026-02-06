# -*- coding: utf-8 -*-
"""
시황 분석 API 라우터
"""
import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import logging
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse, Response
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel

from analysis.market import MarketAnalyzer, market_analyzer
from analysis.news import news_crawler

logger = logging.getLogger(__name__)

# API 호출 시 사용할 analyzer (새로 생성)
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = MarketAnalyzer()
    return _analyzer

router = APIRouter()


class HoldingItem(BaseModel):
    code: str
    name: Optional[str] = None


class AnalysisRequest(BaseModel):
    """holdings: 코드만 문자열 리스트 또는 code+name 리스트. name 있으면 그대로 LLM에 사용."""
    holdings: List[Any] = []  # str (코드) 또는 {"code": str, "name": str}


def _normalize_holdings(holdings: List[Any]) -> Tuple[List[str], Dict[str, str]]:
    """(codes: List[str], names: Dict[str, str]) 로 반환. name 없으면 code 로 채움."""
    codes = []
    names = {}
    for h in holdings or []:
        if isinstance(h, str):
            codes.append(h)
            names[h] = h
        elif isinstance(h, dict):
            c = h.get("code")
            if not c:
                continue
            codes.append(c)
            names[c] = (h.get("name") or c)
        else:
            continue
    return codes, names


@router.get("/news")
async def get_news() -> List[Dict[str, Any]]:
    """뉴스 목록 조회"""
    try:
        news = market_analyzer.get_news(limit=15)
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/stock/{code}")
async def get_stock_news(code: str) -> List[Dict[str, Any]]:
    """특정 종목 뉴스 조회"""
    try:
        news = news_crawler.get_stock_news(code, limit=10)
        return [n.to_dict() for n in news]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/generate", methods=["OPTIONS"])
async def generate_options():
    """CORS preflight: OPTIONS 요청 시 200 반환 (400 방지)"""
    return Response(status_code=200)


@router.post("/generate")
async def generate_analysis(request: Optional[AnalysisRequest] = Body(None)) -> Dict[str, Any]:
    """AI 시황 분석 생성. holdings에 code+name 넣으면 종목명 그대로 사용."""
    holdings_raw = request.holdings if request else None
    codes, holdings_names = _normalize_holdings(holdings_raw) if holdings_raw else ([], {})
    try:
        analyzer = get_analyzer()
        print(f"[API] Analyzer client: {analyzer.client is not None}")
        analysis = analyzer.generate_analysis(user_holdings=codes if codes else None, holdings_names=holdings_names or None)
        return analysis.to_dict()
    except Exception as e:
        logger.exception("generate_analysis failed: %s", e)
        try:
            analyzer = get_analyzer()
            indices, news, technical_indicators, _ = analyzer._collect_market_data(codes if codes else None)
            mock = analyzer._generate_mock_analysis(indices, news, technical_indicators, codes if codes else None)
            return mock.to_dict()
        except Exception as fallback_e:
            logger.exception("mock fallback failed: %s", fallback_e)
            raise HTTPException(status_code=500, detail=str(e))


class StreamAnalysisRequest(BaseModel):
    holdings: List[Any] = []  # [ { code, name }, ... ] 또는 [ "code", ... ]


@router.api_route("/generate/stream", methods=["OPTIONS"])
async def stream_options():
    return Response(status_code=200)


@router.get("/generate/stream")
async def generate_analysis_stream_get(holdings: str = None):
    """GET: holdings=code1,code2 또는 code1:종목명,code2:종목명 (프록시/405 회피용)"""
    if not holdings:
        return await _stream_response(None, None)
    parts = [p.strip() for p in holdings.split(",") if p.strip()]
    codes = []
    names = {}
    for p in parts:
        if ":" in p:
            code, name = p.split(":", 1)
            code, name = code.strip(), name.strip()
            if code:
                codes.append(code)
                names[code] = name or code
        else:
            if p:
                codes.append(p)
                names[p] = p
    return await _stream_response(codes if codes else None, names if names else None)


@router.post("/generate/stream")
async def generate_analysis_stream_post(request: Optional[StreamAnalysisRequest] = Body(None)):
    """POST: body에 holdings: [{ code, name }, ...] 넣으면 포트폴리오와 동일한 종목명 사용."""
    raw = request.holdings if request else None
    codes, holdings_names = _normalize_holdings(raw) if raw else ([], {})
    return await _stream_response(codes if codes else None, holdings_names or None)


async def _stream_response(holdings_list: Optional[List[str]], holdings_names: Optional[Dict[str, str]]):
    """스트리밍 공통 응답"""
    try:
        analyzer = get_analyzer()
        print(f"[API] Stream - holdings_list: {holdings_list}, names: {list((holdings_names or {}).keys())}")
        return StreamingResponse(
            analyzer.generate_analysis_stream(holdings_list, holdings_names=holdings_names),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_indices_for_analysis() -> List[Dict[str, Any]]:
    """분석용 지수 조회"""
    try:
        indices = market_analyzer.get_market_indices()
        return [
            {
                "name": idx.name,
                "value": idx.value,
                "change": idx.change,
                "changePercent": idx.change_percent
            }
            for idx in indices
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
