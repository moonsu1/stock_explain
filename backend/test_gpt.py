# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

r = requests.post('http://localhost:8000/api/analysis/generate', json={})
data = r.json()

print('=== GPT 분석 결과 ===')
print(f"요약: {data.get('summary', '')}")
print(f"코스피: {data.get('kospiAnalysis', '')}")
print(f"코스닥: {data.get('kosdaqAnalysis', '')}")
print(f"나스닥: {data.get('nasdaqAnalysis', '')}")
print(f"추천: {data.get('recommendation', '')}")
print(f"생성시간: {data.get('generatedAt', '')}")
