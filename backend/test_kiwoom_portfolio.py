#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키움 포트폴리오 실제 연동 테스트.

실행: backend 디렉터리에서
  python test_kiwoom_portfolio.py

.env에 KIWOOM_APPKEY, KIWOOM_SECRETKEY가 있어야 함.
실제 계좌/보유종목이 오면 성공(exit 0), 모의 데이터면 실패(exit 1).
"""
import os
import sys

# backend 기준 .env 로드 (import 전에 필요)
def _load_env():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
    os.chdir(backend_dir)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

_load_env()

# 모의 데이터와 동일한지 판별하기 위한 상수 (api.py _get_mock_* 와 동일)
MOCK_ACCOUNT = {
    "total_deposit": 5_000_000,
    "total_evaluation": 15_250_000,
    "total_profit": 1_250_000,
    "profit_percent": 8.93,
}
MOCK_HOLDINGS_FIRST = {
    "code": "233740",
    "name": "KODEX 코스닥150 레버리지",
    "quantity": 100,
    "avg_price": 8500,
    "current_price": 9200,
    "profit": 70000,
    "profit_percent": 8.24,
}


def is_mock_account(account) -> bool:
    if not account:
        return True
    return (
        getattr(account, "total_deposit", None) == MOCK_ACCOUNT["total_deposit"]
        and getattr(account, "total_evaluation", None) == MOCK_ACCOUNT["total_evaluation"]
        and getattr(account, "total_profit", None) == MOCK_ACCOUNT["total_profit"]
        and getattr(account, "profit_percent", None) == MOCK_ACCOUNT["profit_percent"]
    )


def is_mock_holdings(holdings) -> bool:
    if not holdings or len(holdings) < 3:
        return True
    h = holdings[0]
    return (
        getattr(h, "code", None) == MOCK_HOLDINGS_FIRST["code"]
        and getattr(h, "name", None) == MOCK_HOLDINGS_FIRST["name"]
        and getattr(h, "quantity", None) == MOCK_HOLDINGS_FIRST["quantity"]
        and getattr(h, "avg_price", None) == MOCK_HOLDINGS_FIRST["avg_price"]
        and getattr(h, "current_price", None) == MOCK_HOLDINGS_FIRST["current_price"]
        and getattr(h, "profit", None) == MOCK_HOLDINGS_FIRST["profit"]
        and getattr(h, "profit_percent", None) == MOCK_HOLDINGS_FIRST["profit_percent"]
    )


def main():
    from kiwoom.api import kiwoom_api, KIWOOM_AVAILABLE

    print("=" * 60)
    print("키움 포트폴리오 연동 테스트")
    print("=" * 60)
    print(f"KIWOOM_AVAILABLE: {KIWOOM_AVAILABLE}")
    print(f"KIWOOM_APPKEY 설정: {bool(os.getenv('KIWOOM_APPKEY') or os.getenv('KIWOOM_API_KEY'))}")
    print(f"KIWOOM_SECRETKEY 설정: {bool(os.getenv('KIWOOM_SECRETKEY') or os.getenv('KIWOOM_API_SECRET'))}")
    print()

    if not KIWOOM_AVAILABLE:
        print("[FAIL] 키움 API 사용 불가 (패키지 또는 키 미설정)")
        return 1

    # 1) 연결
    ok = kiwoom_api.connect()
    print(f"connect() => {ok}")
    if not ok:
        print("[FAIL] connect() 실패")
        return 1
    print(f"_api 타입: {type(kiwoom_api._api).__name__ if kiwoom_api._api else 'None'}")
    print()

    # 2) 계좌 정보
    account = kiwoom_api.get_account_info()
    print("--- get_account_info() ---")
    print(f"  account_no: {account.account_no}")
    print(f"  total_deposit: {account.total_deposit}")
    print(f"  total_evaluation: {account.total_evaluation}")
    print(f"  total_profit: {account.total_profit}")
    print(f"  profit_percent: {account.profit_percent}")
    account_is_mock = is_mock_account(account)
    print(f"  => {'MOCK (고정값)' if account_is_mock else 'REAL'}")
    print()

    # 3) 보유 종목
    holdings = kiwoom_api.get_holdings()
    print("--- get_holdings() ---")
    print(f"  종목 수: {len(holdings)}")
    for i, h in enumerate(holdings[:5]):
        print(f"  [{i}] {h.code} {h.name} 수량={h.quantity} 평가={h.current_price} 손익={h.profit} ({h.profit_percent}%)")
    if len(holdings) > 5:
        print(f"  ... 외 {len(holdings) - 5}종목")
    holdings_is_mock = is_mock_holdings(holdings)
    print(f"  => {'MOCK (고정 3종목)' if holdings_is_mock else 'REAL'}")
    print()

    # 결과
    if account_is_mock and holdings_is_mock:
        print("[FAIL] 계좌·보유종목 모두 모의 데이터입니다. 실제 연동이 되지 않았습니다.")
        return 1
    print("[OK] 실제 계좌/보유 데이터가 반환되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
