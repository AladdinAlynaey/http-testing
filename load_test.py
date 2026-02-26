"""
Load Testing Script for HTTP Playground
Tests concurrent request handling
"""
import time
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:5050"

ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/books"),
    ("GET", "/api/menu"),
    ("GET", "/api/tasks"),
    ("GET", "/api/notes"),
    ("GET", "/api/weather?city=tokyo"),
    ("GET", "/api/inventory"),
    ("GET", "/api/blog"),
    ("GET", "/api/echo"),
    ("GET", "/api/info"),
]

def make_request(endpoint_tuple):
    method, path = endpoint_tuple
    url = f"{BASE_URL}{path}"
    start = time.time()
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", "LoadTest/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            elapsed = round((time.time() - start) * 1000, 1)
            return {"url": path, "status": resp.status, "time_ms": elapsed, "success": True}
    except urllib.error.HTTPError as e:
        elapsed = round((time.time() - start) * 1000, 1)
        return {"url": path, "status": e.code, "time_ms": elapsed, "success": e.code < 500}
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 1)
        return {"url": path, "status": 0, "time_ms": elapsed, "success": False, "error": str(e)}

def run_load_test(concurrent_users=200, requests_per_user=5):
    print(f"\n{'='*60}")
    print(f"  HTTP Playground Load Test")
    print(f"  Concurrent Users: {concurrent_users}")
    print(f"  Requests per User: {requests_per_user}")
    print(f"  Total Requests: {concurrent_users * requests_per_user}")
    print(f"{'='*60}\n")

    # Build request list
    all_requests = []
    for _ in range(concurrent_users):
        for j in range(requests_per_user):
            all_requests.append(ENDPOINTS[j % len(ENDPOINTS)])

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request, req) for req in all_requests]
        for future in as_completed(futures):
            results.append(future.result())

    total_time = round(time.time() - start_time, 2)

    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    times = [r["time_ms"] for r in successful]

    print(f"  Results:")
    print(f"  ────────────────────────────────")
    print(f"  Total Requests:      {len(results)}")
    print(f"  Successful:          {len(successful)} ({round(len(successful)/len(results)*100,1)}%)")
    print(f"  Failed:              {len(failed)}")
    print(f"  Total Time:          {total_time}s")
    print(f"  Requests/sec:        {round(len(results)/total_time,1)}")

    if times:
        print(f"  Avg Response Time:   {round(sum(times)/len(times),1)}ms")
        print(f"  Min Response Time:   {round(min(times),1)}ms")
        print(f"  Max Response Time:   {round(max(times),1)}ms")
        sorted_times = sorted(times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        print(f"  P95 Response Time:   {round(p95,1)}ms")
        print(f"  P99 Response Time:   {round(p99,1)}ms")

    if failed:
        print(f"\n  Failed requests sample:")
        for f in failed[:5]:
            print(f"    {f['url']} -> {f.get('status', 'N/A')} ({f.get('error', 'unknown')})")

    success_rate = len(successful) / len(results) * 100
    print(f"\n  {'✅ PASS' if success_rate >= 95 else '❌ FAIL'} — {round(success_rate,1)}% success rate")
    print(f"{'='*60}\n")
    return success_rate >= 95

if __name__ == "__main__":
    # Test with increasing concurrency
    for users in [50, 100, 200]:
        run_load_test(concurrent_users=users, requests_per_user=3)
        time.sleep(2)
