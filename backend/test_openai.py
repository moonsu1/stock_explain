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

from openai import OpenAI
client = OpenAI(api_key=api_key)

print("Testing gpt-5-nano...")
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": "Say hello in Korean"}],
    max_completion_tokens=50
)
print(f"Response: {response.choices[0].message.content}")
print(f"Model: {response.model}")
