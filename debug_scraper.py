from duckduckgo_search import DDGS

print("Testing DDGS Connectivity...")
try:
    with DDGS() as ddgs:
        results = list(ddgs.text("test", max_results=3))
        print(f"Results for 'test': {len(results)}")
        if results:
            print(results[0])
except Exception as e:
    print(f"Error: {e}")
