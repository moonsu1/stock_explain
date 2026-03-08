import sys
sys.stdout.reconfigure(encoding='utf-8')
from tools.web_search_tool import fetch_huggingface_papers, fetch_venturebeat_ai, fetch_google_news_rss

print("=== HuggingFace Papers ===")
hf = fetch_huggingface_papers(max_items=3)
print(f"수집: {len(hf)}개")
for item in hf:
    print(f"  - {item['title'][:70]}")

print("\n=== VentureBeat AI ===")
vb = fetch_venturebeat_ai(max_items=3)
print(f"수집: {len(vb)}개")
for item in vb:
    print(f"  - {item['title'][:70]}")

print("\n=== Google News RSS ===")
gn = fetch_google_news_rss("AI agent 2026", max_items=3)
print(f"수집: {len(gn)}개")
for item in gn:
    print(f"  - {item['title'][:70]}")
