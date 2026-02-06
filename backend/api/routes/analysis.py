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
from typing import List, Dict, Any, Optional
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


class AnalysisRequest(BaseModel):
    holdings: List[str] = []


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
    """AI 시황 분석 생성 (body 없음/빈 body 시 holdings=[] 로 진행)"""
    holdings = request.holdings if request else None
    try:
        analyzer = get_analyzer()
        print(f"[API] Analyzer client: {analyzer.client is not None}")
        analysis = analyzer.generate_analysis(holdings)
        return analysis.to_dict()
    except Exception as e:
        logger.exception("generate_analysis failed: %s", e)
        try:
            analyzer = get_analyzer()
            indices, news, technical_indicators, _ = analyzer._collect_market_data(holdings)
            mock = analyzer._generate_mock_analysis(indices, news, technical_indicators, holdings)
            return mock.to_dict()
        except Exception as fallback_e:
            logger.exception("mock fallback failed: %s", fallback_e)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/stream")
async def generate_analysis_stream(holdings: str = None):
    """AI 시황 분석 스트리밍 생성 (SSE)"""
    print(f"[API] ========== Stream endpoint called ==========")
    try:
        analyzer = get_analyzer()
        print(f"[API] Stream - Analyzer client: {analyzer.client is not None}")
        print(f"[API] Stream - Holdings: {holdings}")
        
        holdings_list = holdings.split(",") if holdings else None
        
        return StreamingResponse(
            analyzer.generate_analysis_stream(holdings_list),
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
