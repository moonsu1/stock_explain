# -*- coding: utf-8 -*-
"""
매매 API 라우터
"""
import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

# 키움 API는 선택적 임포트
try:
    from kiwoom.api import kiwoom_api
    from kiwoom.trader import auto_trader, TradingStrategy
    KIWOOM_AVAILABLE = True
except:
    KIWOOM_AVAILABLE = False
    auto_trader = None

router = APIRouter()


class OrderRequest(BaseModel):
    code: str
    quantity: int
    price: int = 0
    order_type: str = "buy"


class StrategyCreate(BaseModel):
    name: str
    stock_code: str
    stock_name: str
    buy_conditions: List[Dict[str, Any]]
    sell_conditions: List[Dict[str, Any]]
    max_amount: int
    loss_cut_percent: float = -3.0
    profit_take_percent: float = 5.0


class StrategyUpdate(BaseModel):
    name: str = None
    enabled: bool = None
    buy_conditions: List[Dict[str, Any]] = None
    sell_conditions: List[Dict[str, Any]] = None
    max_amount: int = None
    loss_cut_percent: float = None
    profit_take_percent: float = None


# 모의 전략 저장소
mock_strategies = [
    {
        "id": "default_1",
        "name": "KODEX 코스닥150 레버리지 전략",
        "enabled": False,
        "stockCode": "233740",
        "stockName": "KODEX 코스닥150레버리지",
        "buyConditions": [{"type": "rsi_below", "value": 30}],
        "sellConditions": [{"type": "rsi_above", "value": 70}],
        "maxAmount": 1000000,
        "lossCutPercent": -3.0,
        "profitTakePercent": 5.0
    }
]

mock_history = [
    {"id": "1", "timestamp": "2026-02-05 14:23:15", "order_type": "buy", "stock_code": "233740", "stock_name": "KODEX 코스닥150레버리지", "quantity": 50, "price": 17000, "reason": "RSI 28, buy signal", "strategy_id": "default_1"},
    {"id": "2", "timestamp": "2026-02-04 10:05:32", "order_type": "sell", "stock_code": "233740", "stock_name": "KODEX 코스닥150레버리지", "quantity": 30, "price": 17500, "reason": "RSI 72, sell signal", "strategy_id": "default_1"},
]


@router.post("/order")
async def place_order(request: OrderRequest) -> Dict[str, Any]:
    """주문 실행"""
    if KIWOOM_AVAILABLE:
        try:
            order_type_num = 1 if request.order_type == "buy" else 2
            price_type = "03" if request.price == 0 else "00"
            
            result = kiwoom_api.send_order(
                order_type=order_type_num,
                code=request.code,
                quantity=request.quantity,
                price=request.price,
                price_type=price_type
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "success": True,
        "message": f"Mock order: {request.order_type} {request.quantity} shares of {request.code}",
        "order_no": f"MOCK{uuid.uuid4().hex[:8].upper()}"
    }


@router.get("/auto/status")
async def get_auto_trade_status() -> Dict[str, Any]:
    """자동매매 상태 조회"""
    if auto_trader:
        return {
            "running": auto_trader.is_running(),
            "activeStrategies": len([s for s in auto_trader.get_strategies() if s.enabled]),
            "totalStrategies": len(auto_trader.get_strategies())
        }
    
    active = len([s for s in mock_strategies if s.get("enabled")])
    return {
        "running": False,
        "activeStrategies": active,
        "totalStrategies": len(mock_strategies)
    }


@router.post("/auto/start")
async def start_auto_trade() -> Dict[str, Any]:
    """자동매매 시작"""
    if auto_trader:
        success = auto_trader.start()
        return {"success": success, "message": "Started" if success else "Already running"}
    
    return {"success": True, "message": "Mock auto-trade started"}


@router.post("/auto/stop")
async def stop_auto_trade() -> Dict[str, Any]:
    """자동매매 중지"""
    if auto_trader:
        success = auto_trader.stop()
        return {"success": success, "message": "Stopped"}
    
    return {"success": True, "message": "Mock auto-trade stopped"}


@router.get("/strategies")
async def get_strategies() -> List[Dict[str, Any]]:
    """전략 목록 조회"""
    if auto_trader:
        strategies = auto_trader.get_strategies()
        return [
            {
                "id": s.id,
                "name": s.name,
                "enabled": s.enabled,
                "stockCode": s.stock_code,
                "stockName": s.stock_name,
                "buyConditions": s.buy_conditions,
                "sellConditions": s.sell_conditions,
                "maxAmount": s.max_amount,
                "lossCutPercent": s.loss_cut_percent,
                "profitTakePercent": s.profit_take_percent
            }
            for s in strategies
        ]
    
    return mock_strategies


@router.post("/strategies")
async def create_strategy(request: StrategyCreate) -> Dict[str, Any]:
    """전략 생성"""
    strategy_id = str(uuid.uuid4())[:8]
    
    if auto_trader:
        strategy = TradingStrategy(
            id=strategy_id,
            name=request.name,
            enabled=False,
            stock_code=request.stock_code,
            stock_name=request.stock_name,
            buy_conditions=request.buy_conditions,
            sell_conditions=request.sell_conditions,
            max_amount=request.max_amount,
            loss_cut_percent=request.loss_cut_percent,
            profit_take_percent=request.profit_take_percent
        )
        success = auto_trader.add_strategy(strategy)
        return {"success": success, "id": strategy_id}
    
    new_strategy = {
        "id": strategy_id,
        "name": request.name,
        "enabled": False,
        "stockCode": request.stock_code,
        "stockName": request.stock_name,
        "buyConditions": request.buy_conditions,
        "sellConditions": request.sell_conditions,
        "maxAmount": request.max_amount,
        "lossCutPercent": request.loss_cut_percent,
        "profitTakePercent": request.profit_take_percent
    }
    mock_strategies.append(new_strategy)
    return {"success": True, "id": strategy_id}


@router.put("/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: StrategyUpdate) -> Dict[str, Any]:
    """전략 수정"""
    if auto_trader:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        success = auto_trader.update_strategy(strategy_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"success": True}
    
    for s in mock_strategies:
        if s["id"] == strategy_id:
            if request.name is not None:
                s["name"] = request.name
            if request.enabled is not None:
                s["enabled"] = request.enabled
            return {"success": True}
    
    raise HTTPException(status_code=404, detail="Strategy not found")


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str) -> Dict[str, Any]:
    """전략 삭제"""
    if auto_trader:
        success = auto_trader.delete_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"success": True}
    
    global mock_strategies
    mock_strategies = [s for s in mock_strategies if s["id"] != strategy_id]
    return {"success": True}


@router.post("/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str) -> Dict[str, Any]:
    """전략 활성화/비활성화 토글"""
    if auto_trader:
        success = auto_trader.toggle_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"success": True}
    
    for s in mock_strategies:
        if s["id"] == strategy_id:
            s["enabled"] = not s.get("enabled", False)
            return {"success": True}
    
    raise HTTPException(status_code=404, detail="Strategy not found")


@router.get("/history")
async def get_trade_history(limit: int = 50) -> List[Dict[str, Any]]:
    """거래 이력 조회"""
    if auto_trader:
        history = auto_trader.get_trade_history(limit)
        return [h.to_dict() for h in history]
    
    return mock_history[:limit]
