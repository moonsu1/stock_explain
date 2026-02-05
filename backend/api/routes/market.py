# -*- coding: utf-8 -*-
"""
시장 정보 API 라우터
"""
import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, time

from analysis.crawler import get_all_indices, get_stock_price, get_commodities_and_world

router = APIRouter()


@router.get("/indices")
async def get_indices() -> List[Dict[str, Any]]:
    """주요 지수 조회"""
    try:
        indices = get_all_indices()
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


@router.get("/stock/{code}")
async def get_stock_info(code: str) -> Dict[str, Any]:
    """종목 정보 조회"""
    try:
        stock = get_stock_price(code)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities")
async def get_commodities() -> List[Dict[str, Any]]:
    """원자재 및 해외 지수 조회 (금, 은, 구리, 니케이)"""
    try:
        items = get_commodities_and_world()
        return [
            {
                "name": item.name,
                "value": item.value,
                "change": item.change,
                "changePercent": item.change_percent
            }
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_market_status() -> Dict[str, Any]:
    """시장 상태 조회"""
    now = datetime.now()
    market_open = time(9, 0)
    market_close = time(15, 30)
    
    is_open = market_open <= now.time() <= market_close
    weekday = now.weekday()
    
    # 주말 체크
    if weekday >= 5:
        is_open = False
        status = "Weekend"
    elif is_open:
        status = "Market Open"
    elif now.time() < market_open:
        status = "Pre-market"
    else:
        status = "Market Closed"
    
    return {
        "isOpen": is_open,
        "status": status,
        "currentTime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "openTime": "09:00",
        "closeTime": "15:30"
    }
