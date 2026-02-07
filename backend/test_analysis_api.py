# -*- coding: utf-8 -*-
"""
구조화/실시간 분석 API 검증: mock 여부 및 보유 종목 전략 필드 확인
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_structured_analysis():
    from analysis.market import MarketAnalyzer
    analyzer = MarketAnalyzer()
    holdings_codes = ["233740", "005930", "000660"]
    holdings_names = {"233740": "KODEX 코스닥150 레버리지", "005930": "삼성전자", "000660": "SK하이닉스"}
    print("[1] 구조화 분석 generate_analysis() 호출...")
    try:
        analysis = analyzer.generate_analysis(user_holdings=holdings_codes, holdings_names=holdings_names)
        d = analysis.to_dict()
    except Exception as e:
        print(f"    실패: {e}")
        return None
    print(f"    summary 길이: {len(d.get('summary', ''))}")
    print(f"    holdingsStrategy 길이: {len(d.get('holdingsStrategy', ''))}")
    hs = d.get("holdingsStrategy")
    if hs is not None and not isinstance(hs, str):
        hs = json.dumps(hs, ensure_ascii=False)
    hs = hs or ""
    is_mock_phrase = "보유 종목이 있으면 RSI와 추세에 따라" in hs
    has_per_stock = "삼성전자" in hs or "005930" in hs or "SK하이닉스" in hs or "233740" in hs
    print(f"    holdingsStrategy 타입: {type(d.get('holdingsStrategy'))}, 길이: {len(hs)}")
    print(f"    holdingsStrategy에 mock 문구 포함: {is_mock_phrase}")
    print(f"    holdingsStrategy에 종목명/코드 포함: {has_per_stock}")
    if hs:
        print(f"    holdingsStrategy 앞 300자: {hs[:300]}...")
    return {"is_mock_phrase": is_mock_phrase, "has_per_stock": has_per_stock, "holdingsStrategy": hs, "isMock": d.get("isMock")}


def test_streaming_holdings_section():
    from analysis.market import MarketAnalyzer
    analyzer = MarketAnalyzer()
    holdings_codes = ["233740", "005930", "000660"]
    holdings_names = {"233740": "KODEX 코스닥150 레버리지", "005930": "삼성전자", "000660": "SK하이닉스"}
    print("\n[2] 실시간(스트리밍) 분석 - 전체 스트림 수집 후 보유 종목 섹션 확인...")
    try:
        gen = analyzer.generate_analysis_stream(holdings_codes, holdings_names=holdings_names)
        collected = []
        for chunk in gen:
            if not isinstance(chunk, str):
                continue
            if chunk.startswith("data: ") and not chunk.startswith("data: [") and chunk.strip() not in ("data: ", "data:"):
                payload = chunk[6:].strip()
                if payload and payload != "[DONE]":
                    collected.append(payload)
        text = " ".join(collected)
    except Exception as e:
        print(f"    실패: {e}")
        import traceback
        traceback.print_exc()
        return None
    print(f"    수집 텍스트 길이: {len(text)}")
    has_holdings_section = "보유 종목" in text or "전망" in text
    has_per_stock = "삼성전자" in text or "005930" in text or "SK하이닉스" in text or "233740" in text or "KODEX" in text
    mock_phrase = "보유 종목이 있으면 RSI와 추세에 따라" in text
    print(f"    보유 종목/전망 관련 텍스트 있음: {has_holdings_section}")
    print(f"    종목명/코드 포함: {has_per_stock}")
    print(f"    mock 문구 포함: {mock_phrase}")
    if text:
        print(f"    샘플 300자: {text[:300]}...")
    return {"has_holdings_section": has_holdings_section, "has_per_stock": has_per_stock, "mock_phrase": mock_phrase}


def main():
    print("=" * 60)
    print("[분석 API 검증] 구조화 / 실시간 mock·실제 구분 테스트")
    print("=" * 60)
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_API_KEY", "").startswith("sk-"):
        print("\n[경고] OPENAI_API_KEY 미설정 또는 비정상. 구조화 분석은 mock으로 나올 수 있음.")
    else:
        print("\n[OK] OPENAI_API_KEY 설정됨")
    r1 = test_structured_analysis()
    r2 = test_streaming_holdings_section()
    print("\n" + "=" * 60)
    print("[결과 요약]")
    if r1:
        if r1.get("is_mock_phrase") or (not r1.get("has_per_stock") and r1.get("holdingsStrategy")):
            print("  구조화 분석: 보유 종목 전략이 mock 또는 종목별 미포함 → 개선 필요")
        else:
            print("  구조화 분석: 보유 종목 전략에 종목별 내용 포함 → 정상")
    else:
        print("  구조화 분석: 호출 실패")
    if r2:
        if r2.get("mock_phrase") or (r2.get("has_holdings_section") and not r2.get("has_per_stock")):
            print("  실시간 분석: 보유 종목 섹션이 mock 또는 종목별 미포함 → 개선 필요")
        else:
            print("  실시간 분석: 보유 종목 섹션에 종목별 내용 포함 → 정상")
    else:
        print("  실시간 분석: 호출 실패 또는 미수집")
    print("=" * 60)


if __name__ == "__main__":
    main()
