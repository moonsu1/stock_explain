# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

# .env 파일 직접 읽기
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            api_key = line.strip().split('=', 1)[1]
            break

print(f"Key from .env: {api_key[:30]}...")

import httpx
from openai import OpenAI
# httpx 0.28+는 proxies 인자 미지원 → openai 내부 전달 시 에러 방지
client = OpenAI(api_key=api_key, http_client=httpx.Client())

print("Testing gpt-5-nano...")
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": "Say hello in Korean"}],
    max_completion_tokens=50
)
print(f"Response: {response.choices[0].message.content}")
print(f"Model: {response.model}")
