"""
키움증권 Open API+ 연동 모듈

주의사항:
- Windows 32비트 Python에서만 동작
- 키움증권 Open API+ 설치 필요
- 영웅문 로그인 상태에서만 API 호출 가능
"""
import os
import sys
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# 키움 API는 Windows에서만 동작
try:
    from pykiwoom.kiwoom import Kiwoom
    KIWOOM_AVAILABLE = True
except ImportError:
    KIWOOM_AVAILABLE = False
    print("⚠️ pykiwoom 미설치 또는 Windows가 아닙니다. 모의 모드로 동작합니다.")


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
    total_deposit: int  # 예수금
    total_evaluation: int  # 총평가금액
    total_profit: int  # 총손익
    profit_percent: float  # 수익률


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


class KiwoomAPI:
    """키움증권 API 래퍼 클래스"""
    
    def __init__(self):
        self.kiwoom: Optional[Kiwoom] = None
        self.connected = False
        self.account_no = os.getenv("KIWOOM_ACCOUNT_NO", "")
        
    def connect(self) -> bool:
        """키움증권 서버에 연결 (로그인)"""
        if not KIWOOM_AVAILABLE:
            print("⚠️ 키움 API 사용 불가. 모의 데이터를 반환합니다.")
            self.connected = True
            return True
            
        try:
            self.kiwoom = Kiwoom()
            self.kiwoom.CommConnect()
            self.connected = True
            
            # 계좌번호 조회
            accounts = self.kiwoom.GetLoginInfo("ACCNO")
            if accounts:
                self.account_no = accounts.split(';')[0]
                
            print(f"✅ 키움증권 연결 성공. 계좌번호: {self.account_no}")
            return True
        except Exception as e:
            print(f"❌ 키움증권 연결 실패: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """연결 해제"""
        self.connected = False
        self.kiwoom = None
        
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.connected
    
    def get_account_info(self) -> AccountInfo:
        """계좌 정보 조회"""
        if not KIWOOM_AVAILABLE or not self.kiwoom:
            # 모의 데이터 반환
            return AccountInfo(
                account_no=f"********{self.account_no[-4:]}" if len(self.account_no) >= 4 else "********1234",
                total_deposit=5000000,
                total_evaluation=15250000,
                total_profit=1250000,
                profit_percent=8.93
            )
            
        try:
            # opw00018: 계좌평가잔고내역요청
            df = self.kiwoom.block_request(
                "opw00018",
                계좌번호=self.account_no,
                비밀번호="",
                비밀번호입력매체구분="00",
                조회구분=2,
                output="계좌평가결과",
                next=0
            )
            
            if df is not None and len(df) > 0:
                return AccountInfo(
                    account_no=f"********{self.account_no[-4:]}",
                    total_deposit=int(df['예수금'].iloc[0].replace(',', '')),
                    total_evaluation=int(df['총평가금액'].iloc[0].replace(',', '')),
                    total_profit=int(df['총평가손익금액'].iloc[0].replace(',', '')),
                    profit_percent=float(df['총수익률(%)'].iloc[0])
                )
        except Exception as e:
            print(f"❌ 계좌 정보 조회 실패: {e}")
            
        return self._get_mock_account_info()
    
    def get_holdings(self) -> List[HoldingStock]:
        """보유 종목 조회"""
        if not KIWOOM_AVAILABLE or not self.kiwoom:
            return self._get_mock_holdings()
            
        try:
            # opw00018: 계좌평가잔고내역요청
            df = self.kiwoom.block_request(
                "opw00018",
                계좌번호=self.account_no,
                비밀번호="",
                비밀번호입력매체구분="00",
                조회구분=2,
                output="계좌평가잔고개별합산",
                next=0
            )
            
            holdings = []
            if df is not None:
                for _, row in df.iterrows():
                    holdings.append(HoldingStock(
                        code=row['종목번호'].strip(),
                        name=row['종목명'].strip(),
                        quantity=int(row['보유수량']),
                        avg_price=int(row['매입가']),
                        current_price=int(row['현재가']),
                        profit=int(row['평가손익']),
                        profit_percent=float(row['수익률(%)'])
                    ))
            return holdings
        except Exception as e:
            print(f"❌ 보유 종목 조회 실패: {e}")
            
        return self._get_mock_holdings()
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """종목 정보 조회"""
        if not KIWOOM_AVAILABLE or not self.kiwoom:
            return self._get_mock_stock_info(code)
            
        try:
            # opt10001: 주식기본정보요청
            df = self.kiwoom.block_request(
                "opt10001",
                종목코드=code,
                output="주식기본정보",
                next=0
            )
            
            if df is not None and len(df) > 0:
                return StockInfo(
                    code=code,
                    name=df['종목명'].iloc[0].strip(),
                    current_price=abs(int(df['현재가'].iloc[0])),
                    change=int(df['전일대비'].iloc[0]),
                    change_percent=float(df['등락율'].iloc[0]),
                    volume=int(df['거래량'].iloc[0])
                )
        except Exception as e:
            print(f"❌ 종목 정보 조회 실패: {e}")
            
        return self._get_mock_stock_info(code)
    
    def get_index(self, index_code: str) -> Dict[str, Any]:
        """지수 조회 (001: 코스피, 101: 코스닥)"""
        if not KIWOOM_AVAILABLE or not self.kiwoom:
            return self._get_mock_index(index_code)
            
        try:
            # opt20001: 업종현재가요청
            df = self.kiwoom.block_request(
                "opt20001",
                시장구분=index_code,
                output="업종현재가",
                next=0
            )
            
            if df is not None and len(df) > 0:
                return {
                    "code": index_code,
                    "name": "코스피" if index_code == "001" else "코스닥",
                    "value": float(df['현재가'].iloc[0]),
                    "change": float(df['전일대비'].iloc[0]),
                    "change_percent": float(df['등락율'].iloc[0])
                }
        except Exception as e:
            print(f"❌ 지수 조회 실패: {e}")
            
        return self._get_mock_index(index_code)
    
    def send_order(
        self,
        order_type: int,  # 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
        code: str,
        quantity: int,
        price: int,
        price_type: str = "00"  # 00:지정가, 03:시장가
    ) -> Dict[str, Any]:
        """주문 전송"""
        if not KIWOOM_AVAILABLE or not self.kiwoom:
            return {
                "success": True,
                "message": "모의 주문 완료",
                "order_no": "MOCK12345"
            }
            
        try:
            order_type_name = "매수" if order_type == 1 else "매도"
            result = self.kiwoom.SendOrder(
                "주식주문",
                "0101",
                self.account_no,
                order_type,
                code,
                quantity,
                price,
                price_type,
                ""
            )
            
            if result == 0:
                return {
                    "success": True,
                    "message": f"{order_type_name} 주문 전송 성공",
                    "order_no": str(result)
                }
            else:
                return {
                    "success": False,
                    "message": f"주문 실패: 에러코드 {result}",
                    "order_no": None
                }
        except Exception as e:
            print(f"❌ 주문 전송 실패: {e}")
            return {
                "success": False,
                "message": str(e),
                "order_no": None
            }
    
    # ===== 모의 데이터 메서드 =====
    
    def _get_mock_account_info(self) -> AccountInfo:
        """모의 계좌 정보"""
        return AccountInfo(
            account_no="********1234",
            total_deposit=5000000,
            total_evaluation=15250000,
            total_profit=1250000,
            profit_percent=8.93
        )
    
    def _get_mock_holdings(self) -> List[HoldingStock]:
        """모의 보유 종목"""
        return [
            HoldingStock(
                code="233740",
                name="KODEX 코스닥150 레버리지",
                quantity=100,
                avg_price=8500,
                current_price=9200,
                profit=70000,
                profit_percent=8.24
            ),
            HoldingStock(
                code="005930",
                name="삼성전자",
                quantity=50,
                avg_price=72000,
                current_price=75000,
                profit=150000,
                profit_percent=4.17
            ),
            HoldingStock(
                code="000660",
                name="SK하이닉스",
                quantity=30,
                avg_price=135000,
                current_price=142000,
                profit=210000,
                profit_percent=5.19
            ),
        ]
    
    def _get_mock_stock_info(self, code: str) -> StockInfo:
        """모의 종목 정보"""
        mock_data = {
            "233740": StockInfo("233740", "KODEX 코스닥150 레버리지", 9200, 150, 1.66, 5280000),
            "005930": StockInfo("005930", "삼성전자", 75000, 500, 0.67, 12500000),
            "000660": StockInfo("000660", "SK하이닉스", 142000, 2000, 1.43, 3200000),
        }
        return mock_data.get(code, StockInfo(code, "알수없음", 10000, 0, 0.0, 0))
    
    def _get_mock_index(self, index_code: str) -> Dict[str, Any]:
        """모의 지수 정보"""
        mock_data = {
            "001": {"code": "001", "name": "코스피", "value": 2650.28, "change": 15.32, "change_percent": 0.58},
            "101": {"code": "101", "name": "코스닥", "value": 862.45, "change": -8.21, "change_percent": -0.94},
        }
        return mock_data.get(index_code, {"code": index_code, "name": "알수없음", "value": 0, "change": 0, "change_percent": 0})


# 싱글톤 인스턴스
kiwoom_api = KiwoomAPI()
