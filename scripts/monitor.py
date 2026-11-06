import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

def check(url, output):
    started = time.perf_counter(); record = {"started_at": datetime.now(timezone.utc).isoformat(), "url": url}
    try:
        with urlopen(url, timeout=10) as response: record.update(status=response.status, ok=response.status == 200, response_ms=round((time.perf_counter() - started) * 1000, 3), error=None)
    except Exception as exc: record.update(status=None, ok=False, response_ms=round((time.perf_counter() - started) * 1000, 3), error=str(exc))
    output.parent.mkdir(parents=True, exist_ok=True); output.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n"); return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--url", default="http://127.0.0.1:8000/health"); parser.add_argument("--interval", type=int, default=30); parser.add_argument("--output", default="reports/monitor.jsonl"); parser.add_argument("--once", action="store_true"); args = parser.parse_args(); output = Path(args.output)
    while True:
        print(json.dumps(check(args.url, output), ensure_ascii=False), flush=True)
        if args.once: break
        time.sleep(max(1, args.interval))
