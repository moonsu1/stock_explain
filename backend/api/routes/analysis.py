# -*- coding: utf-8 -*-
"""
시황 분석 API 라우터
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from typing import List, Dict, Any, Optional, Tuple

from analysis.market import MarketAnalyzer, market_analyzer

logger = logging.getLogger(__name__)

_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = MarketAnalyzer()
    return _analyzer

router = APIRouter()


def _normalize_holdings(holdings: List[Any]) -> Tuple[List[str], Dict[str, str]]:
    """(codes, code->name) 반환. 항목은 str 또는 {"code","name"} dict."""
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
    try:
        return market_analyzer.get_news(limit=15)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/stock/{code}")
async def get_stock_news(code: str) -> List[Dict[str, Any]]:
    try:
        from analysis.news import news_crawler
        news = news_crawler.get_stock_news(code, limit=10)
        return [n.to_dict() for n in news]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/generate", methods=["OPTIONS"])
async def generate_options():
    return Response(status_code=200)


@router.post("/generate")
async def generate_analysis(request: Request) -> Dict[str, Any]:
    """body: { holdings: [ code 또는 { code, name } ] }. 수동 파싱으로 422 방지."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    holdings_raw = body.get("holdings") if isinstance(body, dict) else []
    if not isinstance(holdings_raw, list):
        holdings_raw = []
    codes, holdings_names = _normalize_holdings(holdings_raw)
    try:
        analyzer = get_analyzer()
        analysis = analyzer.generate_analysis(user_holdings=codes if codes else None, holdings_names=holdings_names or None)
        return analysis.to_dict()
    except Exception as e:
        logger.exception("generate_analysis failed: %s", e)
        try:
            analyzer = get_analyzer()
            indices, news, technical_indicators, _ = analyzer._collect_market_data(codes if codes else None)
            mock = analyzer._generate_mock_analysis(indices, news, technical_indicators, codes if codes else None)
            out = mock.to_dict()
            out["isMock"] = True
            return out
        except Exception as fallback_e:
            logger.exception("mock fallback failed: %s", fallback_e)
            raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/generate/stream", methods=["OPTIONS"])
async def stream_options():
    return Response(status_code=200)


@router.get("/generate/stream")
async def generate_analysis_stream(holdings: Optional[str] = None):
    """holdings=code1:이름1,code2:이름2 또는 code1,code2"""
    if not holdings:
        return _stream_response(None, None)
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
    return _stream_response(codes if codes else None, names if names else None)


def _stream_response(holdings_list: Optional[List[str]], holdings_names: Optional[Dict[str, str]]):
    try:
        analyzer = get_analyzer()
        return StreamingResponse(
            analyzer.generate_analysis_stream(holdings_list, holdings_names=holdings_names),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_indices_for_analysis() -> List[Dict[str, Any]]:
    try:
        indices = market_analyzer.get_market_indices()
        return [
            {"name": idx.name, "value": idx.value, "change": idx.change, "changePercent": idx.change_percent}
            for idx in indices
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
