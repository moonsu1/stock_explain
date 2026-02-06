# -*- coding: utf-8 -*-
"""
포트폴리오 API 라우터
"""
import sys
import os
import logging

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 진단용: 모의 데이터와 동일한지 판별 (test_kiwoom_portfolio.py와 동일 기준)
MOCK_ACCOUNT_VALUES = {
    "total_deposit": 5_000_000,
    "total_evaluation": 15_250_000,
    "total_profit": 1_250_000,
    "profit_percent": 8.93,
}
MOCK_HOLDINGS_FIRST = {
    "code": "233740",
    "name": "KODEX 코스닥150레버리지",
    "quantity": 100,
    "avg_price": 8500,
    "current_price": 17110,
    "profit": 861000,
    "profit_percent": 101.29,
}


def _is_mock_account(account) -> bool:
    if not account:
        return True
    return (
        getattr(account, "total_deposit", None) == MOCK_ACCOUNT_VALUES["total_deposit"]
        and getattr(account, "total_evaluation", None) == MOCK_ACCOUNT_VALUES["total_evaluation"]
        and getattr(account, "total_profit", None) == MOCK_ACCOUNT_VALUES["total_profit"]
        and getattr(account, "profit_percent", None) == MOCK_ACCOUNT_VALUES["profit_percent"]
    )


def _is_mock_holdings(holdings) -> bool:
    if not holdings or len(holdings) < 3:
        return True
    h = holdings[0]
    return (
        getattr(h, "code", None) == MOCK_HOLDINGS_FIRST["code"]
        and getattr(h, "quantity", None) == MOCK_HOLDINGS_FIRST["quantity"]
        and getattr(h, "avg_price", None) == MOCK_HOLDINGS_FIRST["avg_price"]
        and getattr(h, "current_price", None) == MOCK_HOLDINGS_FIRST["current_price"]
        and getattr(h, "profit", None) == MOCK_HOLDINGS_FIRST["profit"]
    )

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


@router.get("/egress-ip")
async def get_egress_ip() -> Dict[str, Any]:
    """
    이 서버(백엔드)가 외부로 요청할 때 쓰는 공인 IP를 반환.
    키움 API IP 등록 시 Railway 등 배포 서버 IP를 넣어야 하면,
    배포된 백엔드 URL로 GET /api/portfolio/egress-ip 호출해서 나온 ip를 등록하면 됨.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("https://api.ipify.org?format=json")
            r.raise_for_status()
            data = r.json()
            ip = data.get("ip") or ""
        return {"ip": ip, "message": "키움 개발자센터 IP 등록/현황에 이 IP를 추가하세요."}
    except Exception as e:
        logger.warning("egress-ip check failed: %s", e)
        return {"ip": None, "error": str(e), "message": "IP 조회 실패. api.ipify.org 연결 확인."}


@router.get("/kiwoom-test")
async def kiwoom_test() -> Dict[str, Any]:
    """
    Railway/로컬에서 키움 연동이 실제로 되는지 진단.
    GET https://<your-backend>/api/portfolio/kiwoom-test 로 호출하면
    account_source / holdings_source 가 real 인지 mock 인지와 오류 원인을 반환.
    """
    result = {
        "kiwoom_available": KIWOOM_AVAILABLE,
        "connected": False,
        "account_source": "mock",
        "holdings_source": "mock",
        "error_connect": None,
        "error_account": None,
        "error_holdings": None,
        "message": "",
    }
    if not KIWOOM_AVAILABLE:
        result["message"] = "키움 API 미사용 (패키지 또는 앱키/시크릿 미설정)"
        return result
    try:
        ok = kiwoom_api.connect()
        result["connected"] = ok
        if not ok:
            result["message"] = "connect() 실패"
            return result
    except Exception as e:
        result["error_connect"] = str(e)
        result["message"] = f"connect 예외: {e}"
        logger.exception("kiwoom-test: connect failed")
        return result
    # 계좌
    try:
        account = kiwoom_api.get_account_info()
        result["account_source"] = "mock" if _is_mock_account(account) else "real"
    except Exception as e:
        result["error_account"] = str(e)
        logger.exception("kiwoom-test: get_account_info failed")
    # 보유
    try:
        holdings = kiwoom_api.get_holdings()
        result["holdings_source"] = "mock" if _is_mock_holdings(holdings) else "real"
    except Exception as e:
        result["error_holdings"] = str(e)
        logger.exception("kiwoom-test: get_holdings failed")
    if not result["message"]:
        if result["account_source"] == "real" and result["holdings_source"] == "real":
            result["message"] = "실제 계좌/보유 데이터 반환 중"
        else:
            result["message"] = "연결은 됐으나 계좌/보유는 모의 데이터 (API 응답 확인 필요)"
    return result


@router.get("/summary")
async def get_portfolio_summary() -> Dict[str, Any]:
    """포트폴리오 요약 조회 (예외 시에도 모의 데이터 반환)"""
    try:
        if KIWOOM_AVAILABLE:
            try:
                account = kiwoom_api.get_account_info()
                return {
                    "totalValue": account.total_evaluation,
                    "totalProfit": account.total_profit,
                    "profitPercent": account.profit_percent
                }
            except Exception:
                pass
        account = get_mock_account()
        return {
            "totalValue": account["totalEvaluation"],
            "totalProfit": account["totalProfit"],
            "profitPercent": account["profitPercent"]
        }
    except Exception:
        return {
            "totalValue": 0,
            "totalProfit": 0,
            "profitPercent": 0.0
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
        except Exception as e:
            logger.warning("get_account_info failed, returning mock: %s", e, exc_info=True)
    
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
        except Exception as e:
            logger.warning("get_holdings failed, returning mock: %s", e, exc_info=True)
    
    return get_mock_holdings()
