"""
자동매매 엔진

전략 기반으로 자동으로 매수/매도 주문을 실행합니다.
"""
import os
import json
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, time
from enum import Enum
import threading
import time as time_module

from .api import kiwoom_api, StockInfo


class OrderType(Enum):
    BUY = 1
    SELL = 2


class StrategyCondition(Enum):
    """매매 조건 타입"""
    RSI_BELOW = "rsi_below"  # RSI가 특정 값 이하
    RSI_ABOVE = "rsi_above"  # RSI가 특정 값 이상
    MA_CROSS_UP = "ma_cross_up"  # 이동평균선 상향 돌파
    MA_CROSS_DOWN = "ma_cross_down"  # 이동평균선 하향 돌파
    PRICE_ABOVE = "price_above"  # 특정 가격 이상
    PRICE_BELOW = "price_below"  # 특정 가격 이하
    LOSS_CUT = "loss_cut"  # 손절 (수익률 기준)
    PROFIT_TAKE = "profit_take"  # 익절 (수익률 기준)


@dataclass
class TradingStrategy:
    """매매 전략"""
    id: str
    name: str
    enabled: bool
    stock_code: str
    stock_name: str
    
    # 매수 조건
    buy_conditions: List[Dict[str, Any]]  # [{type: "rsi_below", value: 30}, ...]
    
    # 매도 조건
    sell_conditions: List[Dict[str, Any]]
    
    # 리스크 관리
    max_amount: int  # 최대 투자금액
    loss_cut_percent: float  # 손절 기준 (%)
    profit_take_percent: float  # 익절 기준 (%)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TradingStrategy":
        return cls(**data)


@dataclass
class TradeRecord:
    """거래 기록"""
    id: str
    timestamp: str
    order_type: str  # "buy" or "sell"
    stock_code: str
    stock_name: str
    quantity: int
    price: int
    reason: str
    strategy_id: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AutoTrader:
    """자동매매 엔진"""
    
    def __init__(self):
        self.running = False
        self.strategies: Dict[str, TradingStrategy] = {}
        self.trade_history: List[TradeRecord] = []
        self.thread: Optional[threading.Thread] = None
        self._load_strategies()
        
    def _load_strategies(self):
        """저장된 전략 로드"""
        strategy_file = os.path.join(os.path.dirname(__file__), "..", "data", "strategies.json")
        
        if os.path.exists(strategy_file):
            try:
                with open(strategy_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for s in data:
                        strategy = TradingStrategy.from_dict(s)
                        self.strategies[strategy.id] = strategy
            except Exception as e:
                print(f"⚠️ 전략 로드 실패: {e}")
        else:
            # 기본 전략 생성
            self._create_default_strategy()
    
    def _create_default_strategy(self):
        """기본 전략 생성"""
        default_strategy = TradingStrategy(
            id="default_1",
            name="KODEX 코스닥150 레버리지 전략",
            enabled=False,
            stock_code="233740",
            stock_name="KODEX 코스닥150 레버리지",
            buy_conditions=[
                {"type": "rsi_below", "value": 30},
            ],
            sell_conditions=[
                {"type": "rsi_above", "value": 70},
            ],
            max_amount=1000000,
            loss_cut_percent=-3.0,
            profit_take_percent=5.0
        )
        self.strategies[default_strategy.id] = default_strategy
    
    def _save_strategies(self):
        """전략 저장"""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        
        strategy_file = os.path.join(data_dir, "strategies.json")
        
        try:
            data = [s.to_dict() for s in self.strategies.values()]
            with open(strategy_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 전략 저장 실패: {e}")
    
    def add_strategy(self, strategy: TradingStrategy) -> bool:
        """전략 추가"""
        self.strategies[strategy.id] = strategy
        self._save_strategies()
        return True
    
    def update_strategy(self, strategy_id: str, updates: Dict) -> bool:
        """전략 수정"""
        if strategy_id not in self.strategies:
            return False
            
        strategy = self.strategies[strategy_id]
        for key, value in updates.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
                
        self._save_strategies()
        return True
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """전략 삭제"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            self._save_strategies()
            return True
        return False
    
    def toggle_strategy(self, strategy_id: str) -> bool:
        """전략 활성화/비활성화 토글"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].enabled = not self.strategies[strategy_id].enabled
            self._save_strategies()
            return True
        return False
    
    def get_strategies(self) -> List[TradingStrategy]:
        """모든 전략 조회"""
        return list(self.strategies.values())
    
    def get_trade_history(self, limit: int = 50) -> List[TradeRecord]:
        """거래 이력 조회"""
        return self.trade_history[-limit:]
    
    def start(self) -> bool:
        """자동매매 시작"""
        if self.running:
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("🚀 자동매매 시작")
        return True
    
    def stop(self) -> bool:
        """자동매매 중지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        print("⏹️ 자동매매 중지")
        return True
    
    def is_running(self) -> bool:
        """실행 상태 확인"""
        return self.running
    
    def _run_loop(self):
        """메인 실행 루프"""
        while self.running:
            try:
                # 장 운영 시간 확인 (09:00 ~ 15:30)
                now = datetime.now()
                market_open = time(9, 0)
                market_close = time(15, 30)
                
                if not (market_open <= now.time() <= market_close):
                    print(f"⏰ 장 운영 시간이 아닙니다. 현재 시간: {now.strftime('%H:%M')}")
                    time_module.sleep(60)  # 1분 대기
                    continue
                
                # 활성화된 전략 실행
                for strategy in self.strategies.values():
                    if strategy.enabled:
                        self._execute_strategy(strategy)
                
                # 10초 대기
                time_module.sleep(10)
                
            except Exception as e:
                print(f"❌ 자동매매 에러: {e}")
                time_module.sleep(5)
    
    def _execute_strategy(self, strategy: TradingStrategy):
        """전략 실행"""
        try:
            # 종목 정보 조회
            stock_info = kiwoom_api.get_stock_info(strategy.stock_code)
            if not stock_info:
                return
            
            # 보유 종목 확인
            holdings = kiwoom_api.get_holdings()
            holding = next((h for h in holdings if h.code == strategy.stock_code), None)
            
            # 매수 조건 체크
            if not holding:
                if self._check_buy_conditions(strategy, stock_info):
                    self._execute_buy(strategy, stock_info)
            # 매도 조건 체크
            else:
                if self._check_sell_conditions(strategy, stock_info, holding):
                    self._execute_sell(strategy, stock_info, holding)
                    
        except Exception as e:
            print(f"❌ 전략 실행 에러 ({strategy.name}): {e}")
    
    def _check_buy_conditions(self, strategy: TradingStrategy, stock_info: StockInfo) -> bool:
        """매수 조건 체크"""
        # TODO: 실제 기술적 지표 계산 구현
        # 현재는 모의로 False 반환 (실제 구현 시 RSI, MA 등 계산 필요)
        return False
    
    def _check_sell_conditions(self, strategy: TradingStrategy, stock_info: StockInfo, holding) -> bool:
        """매도 조건 체크"""
        # 손절 체크
        if holding.profit_percent <= strategy.loss_cut_percent:
            return True
            
        # 익절 체크
        if holding.profit_percent >= strategy.profit_take_percent:
            return True
            
        # TODO: 기타 매도 조건 체크
        return False
    
    def _execute_buy(self, strategy: TradingStrategy, stock_info: StockInfo):
        """매수 실행"""
        # 매수 수량 계산
        quantity = strategy.max_amount // stock_info.current_price
        
        if quantity <= 0:
            return
            
        result = kiwoom_api.send_order(
            order_type=1,  # 매수
            code=strategy.stock_code,
            quantity=quantity,
            price=stock_info.current_price,
            price_type="03"  # 시장가
        )
        
        if result["success"]:
            record = TradeRecord(
                id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                order_type="buy",
                stock_code=strategy.stock_code,
                stock_name=strategy.stock_name,
                quantity=quantity,
                price=stock_info.current_price,
                reason="매수 조건 충족",
                strategy_id=strategy.id
            )
            self.trade_history.append(record)
            print(f"✅ 매수 체결: {strategy.stock_name} {quantity}주 @ {stock_info.current_price}원")
    
    def _execute_sell(self, strategy: TradingStrategy, stock_info: StockInfo, holding):
        """매도 실행"""
        result = kiwoom_api.send_order(
            order_type=2,  # 매도
            code=strategy.stock_code,
            quantity=holding.quantity,
            price=stock_info.current_price,
            price_type="03"  # 시장가
        )
        
        if result["success"]:
            reason = "익절" if holding.profit_percent > 0 else "손절"
            record = TradeRecord(
                id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                order_type="sell",
                stock_code=strategy.stock_code,
                stock_name=strategy.stock_name,
                quantity=holding.quantity,
                price=stock_info.current_price,
                reason=f"{reason} ({holding.profit_percent:.2f}%)",
                strategy_id=strategy.id
            )
            self.trade_history.append(record)
            print(f"✅ 매도 체결: {strategy.stock_name} {holding.quantity}주 @ {stock_info.current_price}원 ({reason})")


# 싱글톤 인스턴스
auto_trader = AutoTrader()
