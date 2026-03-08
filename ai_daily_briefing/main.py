"""
AI Daily Briefing — 진입점
매일 오전 7시에 브리핑을 자동으로 실행하고 이메일로 발송합니다.

사용법:
  # 즉시 테스트 실행 (스케줄러 없이)
  python main.py --now

  # 스케줄러 모드 (매일 오전 7시 자동 실행)
  python main.py
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

from agents.orchestrator import run_briefing


def job():
    """스케줄러가 호출하는 브리핑 작업"""
    try:
        run_briefing()
    except Exception as e:
        print(f"[main] 브리핑 실행 중 오류 발생: {e}")


def main():
    if "--now" in sys.argv:
        print("[main] 즉시 실행 모드")
        job()
        return

    hour = int(os.getenv("BRIEFING_HOUR", "8"))
    minute = int(os.getenv("BRIEFING_MINUTE", "0"))

    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        func=job,
        trigger=CronTrigger(hour=hour, minute=minute, timezone="Asia/Seoul"),
        id="daily_briefing",
        name="AI Daily Briefing",
        replace_existing=True,
    )

    print(f"[main] 스케줄러 시작 — 매일 {hour:02d}:{minute:02d} KST 브리핑 발송")
    print("[main] 종료하려면 Ctrl+C")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n[main] 스케줄러 종료")


if __name__ == "__main__":
    main()
