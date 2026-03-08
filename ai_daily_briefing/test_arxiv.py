import sys
sys.stdout.reconfigure(encoding='utf-8')
from tools.arxiv_tool import fetch_papers_for_group

papers = fetch_papers_for_group('agent_system', days_back=7)
print(f"수집된 논문 수: {len(papers)}")
for p in papers:
    print(f"  - [{p['published']}] {p['title'][:70]}")
