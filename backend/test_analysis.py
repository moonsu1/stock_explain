# -*- coding: utf-8 -*-
"""
시황 분석 테스트 스크립트

키움 API 없이 실행 가능!
"""
import os
import sys

# 콘솔 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.crawler import get_all_indices, get_stock_price
from analysis.news import news_crawler
from analysis.market import market_analyzer

def main():
    print("=" * 50)
    print("[시황 분석 테스트] - 키움 API 없이 동작")
    print("=" * 50)
    
    # 1. 지수 조회
    print("\n[주요 지수] - 네이버 금융 크롤링")
    print("-" * 40)
    
    indices = get_all_indices()
    for idx in indices:
        sign = "+" if idx.change >= 0 else ""
        arrow = "(상승)" if idx.change >= 0 else "(하락)"
        print(f"  {idx.name}: {idx.value:,.2f}  {arrow} {sign}{idx.change:,.2f} ({sign}{idx.change_percent:.2f}%)")
    
    # 2. 종목 시세
    print("\n[관심 종목 시세]")
    print("-" * 40)
    
    watch_list = [
        ("233740", "KODEX 코스닥150 레버리지"),
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
    ]
    
    for code, name in watch_list:
        stock = get_stock_price(code)
        if stock:
            sign = "+" if stock['change'] >= 0 else ""
            arrow = "(상승)" if stock['change'] >= 0 else "(하락)"
            print(f"  {stock['name']}: {stock['currentPrice']:,}원  {arrow} {sign}{stock['change']:,} ({sign}{stock['changePercent']:.2f}%)")
        else:
            print(f"  {name}: 조회 실패")
    
    # 3. 뉴스
    print("\n[최신 증시 뉴스]")
    print("-" * 40)
    
    news = news_crawler.get_market_headlines()[:5]
    for i, n in enumerate(news, 1):
        print(f"  {i}. [{n.source}] {n.title}")
    
    # 4. AI 분석 (OpenAI API 키 필요)
    print("\n[AI 시황 분석]")
    print("-" * 40)
    
    if os.getenv("OPENAI_API_KEY"):
        print("  * OpenAI API 연결됨 - GPT 분석 실행 중...")
    else:
        print("  * OPENAI_API_KEY 미설정 - 모의 분석 사용")
    
    analysis = market_analyzer.generate_analysis(["KODEX 코스닥150 레버리지"])
    
    print(f"\n  [요약]")
    print(f"  {analysis.summary}")
    
    print(f"\n  [투자 전략]")
    print(f"  {analysis.recommendation}")
    
    print("\n" + "=" * 50)
    print("[테스트 완료]")
    print("=" * 50)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
