"""
LLM 클라이언트 추상화 레이어
- LLM_PROVIDER=gemini → Gemini 2.0 Flash (기본)
- LLM_PROVIDER=claude → Claude Haiku 4.5 (대안)
LLM_PROVIDER 환경변수만 바꾸면 모델 전환 가능
"""

import os
import time
from dotenv import load_dotenv
from config import GEMINI_MODEL, CLAUDE_MODEL, LLM_REQUEST_DELAY_SEC

load_dotenv()

_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
_gemini_client = None
_anthropic_client = None


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 .env에 설정되지 않았습니다.")
        genai.configure(api_key=api_key)
        _gemini_client = genai.GenerativeModel(GEMINI_MODEL)
    return _gemini_client


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_retries: int = 3,
) -> str:
    """
    LLM_PROVIDER 설정에 따라 Gemini 또는 Claude를 호출합니다.
    Rate limit(429) 발생 시 최대 max_retries회 재시도합니다.
    """
    import re

    for attempt in range(1, max_retries + 1):
        try:
            if _provider == "claude":
                client = _get_anthropic()
                response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                result = response.content[0].text

            else:
                model = _get_gemini()
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 4096,
                    },
                )
                result = response.text

            time.sleep(LLM_REQUEST_DELAY_SEC)
            return result

        except Exception as e:
            err_str = str(e)
            # Rate limit 에러면 retry_delay 값을 파싱해서 대기
            retry_secs = LLM_REQUEST_DELAY_SEC * 5
            match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_str)
            if match:
                retry_secs = int(match.group(1)) + 3

            if attempt < max_retries:
                print(f"  [llm] 호출 실패 (시도 {attempt}/{max_retries}), {retry_secs}초 후 재시도...")
                time.sleep(retry_secs)
            else:
                print(f"  [llm] 최종 실패 ({_provider}): {err_str[:100]}")
                return "[요약 생성 실패 — 재시도 초과]"

    return "[요약 생성 실패]"
