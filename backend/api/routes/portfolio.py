# -*- coding: utf-8 -*-
"""
포트폴리오 API 라우터
"""
import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

# 키움 API는 선택적 임포트
try:
    from kiwoom.api import kiwoom_api
    KIWOOM_AVAILABLE = True
except:
    KIWOOM_AVAILABLE = False

router = APIRouter()


def get_mock_account():
    """모의 계좌 정보"""
    return {
        "accountNo": "********1234",
        "totalDeposit": 5000000,
        "totalEvaluation": 15250000,
        "totalProfit": 1250000,
        "profitPercent": 8.93
    }


def get_mock_holdings():
    """모의 보유 종목"""
    return [
        {
            "code": "233740",
            "name": "KODEX 코스닥150레버리지",
            "quantity": 100,
            "avgPrice": 8500,
            "currentPrice": 17110,
            "profit": 861000,
            "profitPercent": 101.29
        },
        {
            "code": "005930",
            "name": "삼성전자",
            "quantity": 50,
            "avgPrice": 72000,
            "currentPrice": 159300,
            "profit": 4365000,
            "profitPercent": 121.25
        },
        {
            "code": "000660",
            "name": "SK하이닉스",
            "quantity": 30,
            "avgPrice": 135000,
            "currentPrice": 842000,
            "profit": 21210000,
            "profitPercent": 523.70
        },
    ]


@router.post("/connect")
async def connect_kiwoom() -> Dict[str, Any]:
    """키움증권 연결"""
    if KIWOOM_AVAILABLE:
        try:
            success = kiwoom_api.connect()
            return {"success": success, "message": "Connected" if success else "Failed"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    else:
        return {"success": True, "message": "Mock mode (Kiwoom API not available)"}


@router.post("/disconnect")
async def disconnect_kiwoom() -> Dict[str, Any]:
    """키움증권 연결 해제"""
    if KIWOOM_AVAILABLE:
        kiwoom_api.disconnect()
    return {"success": True, "message": "Disconnected"}


@router.get("/status")
async def get_connection_status() -> Dict[str, Any]:
    """연결 상태 조회"""
    if KIWOOM_AVAILABLE:
        return {"connected": kiwoom_api.is_connected()}
    return {"connected": False, "mock": True}


@router.get("/summary")
async def get_portfolio_summary() -> Dict[str, Any]:
    """포트폴리오 요약 조회"""
    if KIWOOM_AVAILABLE:
        try:
            account = kiwoom_api.get_account_info()
            return {
                "totalValue": account.total_evaluation,
                "totalProfit": account.total_profit,
                "profitPercent": account.profit_percent
            }
        except:
            pass
    
    # 모의 데이터
    account = get_mock_account()
    return {
        "totalValue": account["totalEvaluation"],
        "totalProfit": account["totalProfit"],
        "profitPercent": account["profitPercent"]
    }


@router.get("/account")
async def get_account_info() -> Dict[str, Any]:
    """계좌 정보 조회"""
    if KIWOOM_AVAILABLE:
        try:
            account = kiwoom_api.get_account_info()
            return {
                "accountNo": account.account_no,
                "totalDeposit": account.total_deposit,
                "totalEvaluation": account.total_evaluation,
                "totalProfit": account.total_profit,
                "profitPercent": account.profit_percent
            }
        except:
            pass
    
    return get_mock_account()


@router.get("/stocks")
async def get_holdings() -> List[Dict[str, Any]]:
    """보유 종목 조회"""
    if KIWOOM_AVAILABLE:
        try:
            holdings = kiwoom_api.get_holdings()
            return [
                {
                    "code": h.code,
                    "name": h.name,
                    "quantity": h.quantity,
                    "avgPrice": h.avg_price,
                    "currentPrice": h.current_price,
                    "profit": h.profit,
                    "profitPercent": h.profit_percent
                }
                for h in holdings
            ]
        except:
            pass
    
    return get_mock_holdings()
