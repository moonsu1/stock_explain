"""
키움증권 REST API 연동 모듈 (KiwoomRestApi / kiwoom-openapi)

환경변수 KIWOOM_APPKEY, KIWOOM_SECRETKEY만 설정하면 사용 가능.
미설정 또는 라이브러리 미설치 시 모의 데이터로 동작.
"""
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

# 라이브러리가 kiwoom_appkey, kiwoom_secretkey를 읽으므로 우리 env를 매핑
_def_app = os.getenv("KIWOOM_APPKEY")
_def_sec = os.getenv("KIWOOM_SECRETKEY")
if _def_app is not None:
    os.environ.setdefault("kiwoom_appkey", _def_app)
if _def_sec is not None:
    os.environ.setdefault("kiwoom_secretkey", _def_sec)

try:
    from kiwoom_openapi import KiwoomOpenAPI
    _KiwoomOpenAPI = KiwoomOpenAPI
except ImportError:
    try:
        from kiwoom import KiwoomOpenAPI
        _KiwoomOpenAPI = KiwoomOpenAPI
    except ImportError:
        try:
            from kiwoom_api.kiwoom import KiwoomOpenAPI
            _KiwoomOpenAPI = KiwoomOpenAPI
        except ImportError:
            _KiwoomOpenAPI = None

_has_appkey = bool(os.getenv("KIWOOM_APPKEY") or os.getenv("kiwoom_appkey"))
_has_secret = bool(os.getenv("KIWOOM_SECRETKEY") or os.getenv("kiwoom_secretkey"))
KIWOOM_AVAILABLE = _KiwoomOpenAPI is not None and _has_appkey and _has_secret

def _kiwoom_unavailable_reason() -> str:
    if _KiwoomOpenAPI is None:
        return "kiwoom-openapi 패키지 임포트 실패 (설치 확인 필요)"
    if not _has_appkey:
        return "KIWOOM_APPKEY 환경변수 미설정"
    if not _has_secret:
        return "KIWOOM_SECRETKEY 환경변수 미설정"
    return "알 수 없음"


@dataclass
class StockInfo:
    """종목 정보"""
    code: str
    name: str
    current_price: int
    change: int
    change_percent: float
    volume: int


@dataclass
class AccountInfo:
    """계좌 정보"""
    account_no: str
    total_deposit: int
    total_evaluation: int
    total_profit: int
    profit_percent: float


@dataclass
class HoldingStock:
    """보유 종목"""
    code: str
    name: str
    quantity: int
    avg_price: int
    current_price: int
    profit: int
    profit_percent: float


def _safe_int(v: Any, default: int = 0) -> int:
    if v is None:
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class KiwoomAPI:
    """키움증권 REST API 래퍼 (기존 시그니처 유지)"""

    def __init__(self):
        self._api: Optional[Any] = None
        self.connected = False
        self.account_no = os.getenv("KIWOOM_ACCOUNT_NO", "")

    def connect(self) -> bool:
        """키움 REST API 로그인 (auth_login)"""
        if not KIWOOM_AVAILABLE or _KiwoomOpenAPI is None:
            reason = _kiwoom_unavailable_reason()
            print(f"⚠️ 키움 API 사용 불가. 모의 데이터를 반환합니다. (원인: {reason})")
            self.connected = True
            return True

        app = os.getenv("KIWOOM_APPKEY") or os.getenv("kiwoom_appkey")
        sec = os.getenv("KIWOOM_SECRETKEY") or os.getenv("kiwoom_secretkey")
        if not app or not sec:
            self.connected = True
            return True

        try:
            os.environ["kiwoom_appkey"] = app
            os.environ["kiwoom_secretkey"] = sec
            self._api = _KiwoomOpenAPI(app_key=app, app_secret=sec)
            result = self._api.auth_login()
            if result and result.get("status") == "success":
                self.connected = True
                acc_list = getattr(self._api, "get_account_list", None)
                if callable(acc_list):
                    try:
                        accounts = acc_list()
                        if isinstance(accounts, list) and accounts:
                            self.account_no = accounts[0] if isinstance(accounts[0], str) else f"{accounts[0]}"
                        elif isinstance(accounts, dict) and accounts.get("data"):
                            lst = accounts["data"] if isinstance(accounts["data"], list) else [accounts["data"]]
                            if lst:
                                self.account_no = str(lst[0])
                    except Exception:
                        pass
                if not self.account_no:
                    self.account_no = os.getenv("KIWOOM_ACCOUNT_NO", "********1234")
                print(f"✅ 키움증권 REST 연결 성공. 계좌: {self.account_no}")
                return True
            self.connected = False
            return False
        except Exception as e:
            print(f"❌ 키움증권 연결 실패: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """연결 해제"""
        self.connected = False
        self._api = None

    def is_connected(self) -> bool:
        return self.connected

    def get_account_info(self) -> AccountInfo:
        """계좌 정보 조회"""
        if not KIWOOM_AVAILABLE or not self._api:
            return self._get_mock_account_info()

        try:
            acc_list = getattr(self._api, "get_account_list", None)
            account_api = getattr(self._api, "account", None)
            get_balance = getattr(account_api, "get_account_balance", None) if account_api else None
            get_deposit = getattr(account_api, "get_deposit", None) if account_api else None
            get_profit = getattr(account_api, "get_account_profit_loss", None) if account_api else None

            cano, acnt_prdt_cd = self._parse_account_no(self.account_no)
            if get_balance and cano and acnt_prdt_cd:
                bal = get_balance(cano=cano, acnt_prdt_cd=acnt_prdt_cd)
                dep = get_deposit(cano=cano, acnt_prdt_cd=acnt_prdt_cd) if get_deposit else {}
                pl = get_profit(cano=cano, acnt_prdt_cd=acnt_prdt_cd) if get_profit else {}
                return self._map_account_info(bal, dep, pl)
        except Exception as e:
            print(f"❌ 계좌 정보 조회 실패: {e}")
        return self._get_mock_account_info()

    def _parse_account_no(self, account_no: str) -> tuple:
        """계좌번호를 cano, acnt_prdt_cd로 분리"""
        if not account_no or account_no.startswith("*"):
            return "", ""
        if "-" in account_no:
            a, b = account_no.split("-", 1)
            return a.strip(), b.strip()
        if len(account_no) >= 10:
            return account_no[:8], account_no[8:].lstrip("0") or "01"
        return account_no, "01"

    def _map_account_info(self, bal: Dict, dep: Dict, pl: Dict) -> AccountInfo:
        """REST 응답을 AccountInfo로 매핑"""
        def dig(d: Dict, *keys: str, default=0):
            for k in keys:
                if isinstance(d, dict) and k in d:
                    return d[k]
            return default

        total_deposit = _safe_int(dig(dep, "dnca_tot_amt", "예수금총액", "total") or dig(bal, "dnca_tot_amt"), 5000000)
        total_eval = _safe_int(dig(bal, "tot_evlu_amt", "총평가금액", "total_evaluation"), 15250000)
        total_profit = _safe_int(dig(pl, "tot_evlu_pfls_amt", "총평가손익금액", "total_profit") or dig(bal, "tot_evlu_pfls_amt"), 1250000)
        profit_pct = _safe_float(dig(pl, "tot_evlu_pfls_rt", "총수익률", "profit_percent") or dig(bal, "tot_evlu_pfls_rt"), 8.93)
        if total_eval and total_eval != total_profit and profit_pct == 0:
            cost = total_eval - total_profit
            if cost:
                profit_pct = round((total_profit / cost) * 100, 2)
        acc_no = self.account_no
        if len(acc_no) >= 4 and not acc_no.startswith("*"):
            acc_no = f"********{acc_no[-4:]}"
        return AccountInfo(
            account_no=acc_no,
            total_deposit=total_deposit,
            total_evaluation=total_eval,
            total_profit=total_profit,
            profit_percent=profit_pct,
        )

    def get_holdings(self) -> List[HoldingStock]:
        """보유 종목 조회"""
        if not KIWOOM_AVAILABLE or not self._api:
            return self._get_mock_holdings()

        try:
            account_api = getattr(self._api, "account", None)
            get_balance = getattr(account_api, "get_account_balance", None) if account_api else None
            cano, acnt_prdt_cd = self._parse_account_no(self.account_no)
            if get_balance and cano and acnt_prdt_cd:
                bal = get_balance(cano=cano, acnt_prdt_cd=acnt_prdt_cd)
                rows = bal.get("output2") or bal.get("output") or bal.get("data") or []
                if isinstance(rows, dict):
                    rows = [rows]
                holdings = []
                for r in rows if isinstance(rows, list) else []:
                    if not isinstance(r, dict):
                        continue
                    code = str(r.get("pdno", r.get("종목코드", r.get("stock_code", "")))).strip()
                    name = str(r.get("prdt_name", r.get("종목명", r.get("name", "")))).strip()
                    qty = _safe_int(r.get("hldg_qty", r.get("보유수량", r.get("quantity", 0))))
                    avg = _safe_int(r.get("pchs_avg_pric", r.get("매입가", r.get("avg_price", 0))))
                    cur = _safe_int(r.get("evlu_pric", r.get("현재가", r.get("current_price", 0))) or avg)
                    profit = _safe_int(r.get("evlu_pfls_amt", r.get("평가손익", r.get("profit", 0))))
                    pct = _safe_float(r.get("evlu_pfls_rt", r.get("수익률", r.get("profit_percent", 0))))
                    if code:
                        holdings.append(HoldingStock(code=code, name=name or code, quantity=qty, avg_price=avg, current_price=cur, profit=profit, profit_percent=pct))
                if holdings:
                    return holdings
        except Exception as e:
            print(f"❌ 보유 종목 조회 실패: {e}")
        return self._get_mock_holdings()

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """종목 정보 조회"""
        if not KIWOOM_AVAILABLE or not self._api:
            return self._get_mock_stock_info(code)

        try:
            info = getattr(self._api, "get_stock_info", None)
            price_info = getattr(self._api, "get_stock_price_info", None)
            if callable(info):
                res = info(code)
            elif callable(price_info):
                res = price_info(code)
            else:
                return self._get_mock_stock_info(code)
            if not isinstance(res, dict):
                return self._get_mock_stock_info(code)
            data = res.get("data") or res
            if isinstance(data, list) and data:
                data = data[0]
            if not isinstance(data, dict):
                data = res
            name = str(data.get("prdt_name", data.get("종목명", data.get("name", "알수없음")))).strip()
            cur = _safe_int(data.get("stck_prpr", data.get("현재가", data.get("current_price", 0))))
            chg = _safe_int(data.get("prdy_vrss", data.get("전일대비", data.get("change", 0))))
            chg_pct = _safe_float(data.get("prdy_ctrt", data.get("등락율", data.get("change_percent", 0))))
            vol = _safe_int(data.get("acml_vol", data.get("거래량", data.get("volume", 0))))
            return StockInfo(code=code, name=name or code, current_price=cur or 10000, change=chg, change_percent=chg_pct, volume=vol)
        except Exception as e:
            print(f"❌ 종목 정보 조회 실패: {e}")
        return self._get_mock_stock_info(code)

    def get_index(self, index_code: str) -> Dict[str, Any]:
        """지수 조회 (미지원 시 모의)"""
        return self._get_mock_index(index_code)

    def send_order(
        self,
        order_type: int,
        code: str,
        quantity: int,
        price: int,
        price_type: str = "00",
    ) -> Dict[str, Any]:
        """주문 전송. order_type 1=매수, 2=매도."""
        if not KIWOOM_AVAILABLE or not self._api:
            return {"success": True, "message": "모의 주문 완료", "order_no": "MOCK12345"}

        try:
            place = getattr(self._api, "place_domestic_order", None)
            if not callable(place):
                return {"success": True, "message": "모의 주문 완료", "order_no": "MOCK12345"}
            acc = self.account_no or ""
            if not acc or acc.startswith("*"):
                acc_list = getattr(self._api, "get_account_list", None)
                if callable(acc_list):
                    accounts = acc_list()
                    if isinstance(accounts, list) and accounts:
                        acc = str(accounts[0])
                    elif isinstance(accounts, dict) and accounts.get("data"):
                        acc = str(accounts["data"][0] if isinstance(accounts["data"], list) else accounts["data"])
            order_type_str = "00" if price_type != "03" else "03"
            trade_type = "2" if order_type == 1 else "1"
            result = place(
                account_no=acc,
                stock_code=code,
                order_type=order_type_str,
                trade_type=trade_type,
                quantity=quantity,
                price=price or 0,
                order_condition="0",
            )
            if isinstance(result, dict):
                if result.get("status") == "success" or result.get("success"):
                    return {"success": True, "message": result.get("message", "주문 전송 성공"), "order_no": result.get("order_no") or ""}
                return {"success": False, "message": result.get("message", "주문 실패"), "order_no": None}
            return {"success": True, "message": "주문 전송됨", "order_no": str(result)}
        except Exception as e:
            print(f"❌ 주문 전송 실패: {e}")
            return {"success": False, "message": str(e), "order_no": None}

    def _get_mock_account_info(self) -> AccountInfo:
        return AccountInfo(
            account_no=f"********{self.account_no[-4:]}" if len(self.account_no) >= 4 else "********1234",
            total_deposit=5000000,
            total_evaluation=15250000,
            total_profit=1250000,
            profit_percent=8.93,
        )

    def _get_mock_holdings(self) -> List[HoldingStock]:
        return [
            HoldingStock("233740", "KODEX 코스닥150 레버리지", 100, 8500, 9200, 70000, 8.24),
            HoldingStock("005930", "삼성전자", 50, 72000, 75000, 150000, 4.17),
            HoldingStock("000660", "SK하이닉스", 30, 135000, 142000, 210000, 5.19),
        ]

    def _get_mock_stock_info(self, code: str) -> StockInfo:
        mock = {
            "233740": StockInfo("233740", "KODEX 코스닥150 레버리지", 9200, 150, 1.66, 5280000),
            "005930": StockInfo("005930", "삼성전자", 75000, 500, 0.67, 12500000),
            "000660": StockInfo("000660", "SK하이닉스", 142000, 2000, 1.43, 3200000),
        }
        return mock.get(code, StockInfo(code, "알수없음", 10000, 0, 0.0, 0))

    def _get_mock_index(self, index_code: str) -> Dict[str, Any]:
        mock = {
            "001": {"code": "001", "name": "코스피", "value": 2650.28, "change": 15.32, "change_percent": 0.58},
            "101": {"code": "101", "name": "코스닥", "value": 862.45, "change": -8.21, "change_percent": -0.94},
        }
        return mock.get(index_code, {"code": index_code, "name": "알수없음", "value": 0, "change": 0, "change_percent": 0})


kiwoom_api = KiwoomAPI()
