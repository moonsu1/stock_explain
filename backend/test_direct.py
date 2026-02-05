# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True)

from analysis.market import MarketAnalyzer

print("Creating MarketAnalyzer...")
analyzer = MarketAnalyzer()

print(f"\nClient exists: {analyzer.client is not None}")
print(f"Model: {analyzer.model}")

print("\nGenerating analysis...")
result = analyzer.generate_analysis()

print("\n" + "=" * 70)
print("                    AI 시황 분석 리포트")
print("=" * 70)

print(f"\n[요약]")
print(f"  {result.summary}")

print(f"\n[뉴스 분석]")
print(f"  {result.news_analysis}")

print(f"\n[코스피 분석]")
print(f"  {result.kospi_analysis}")

print(f"\n[코스닥 분석]")
print(f"  {result.kosdaq_analysis}")

print(f"\n[나스닥 분석]")
print(f"  {result.nasdaq_analysis}")

print(f"\n[기술적 지표 분석]")
print(f"  종합: {result.technical_summary.overall}")
print(f"  RSI: {result.technical_summary.rsi_status}")
print(f"  볼린저밴드: {result.technical_summary.bollinger_status}")
print(f"  이동평균선: {result.technical_summary.ma_status}")
if result.technical_summary.oversold_stocks:
    print(f"  과매도 종목: {', '.join(result.technical_summary.oversold_stocks)}")
if result.technical_summary.overbought_stocks:
    print(f"  과매수 종목: {', '.join(result.technical_summary.overbought_stocks)}")

print(f"\n[시장 심리]")
print(f"  {result.market_sentiment}")

print(f"\n[유망 테마]")
for i, theme in enumerate(result.hot_themes, 1):
    print(f"  {i}. {theme.name}")
    print(f"     이유: {theme.reason}")
    print(f"     코스피 대장주: {theme.kospi_leader}")
    print(f"     코스닥 대장주: {theme.kosdaq_leader}")

print(f"\n[리스크 요인]")
for risk in result.risk_factors:
    print(f"  - {risk}")

print(f"\n[액션 아이템]")
for action in result.action_items:
    print(f"  - {action}")

print(f"\n[투자 전략 제안]")
print(f"  {result.recommendation}")

print(f"\n[생성 시간: {result.generated_at}]")
print("=" * 70)
