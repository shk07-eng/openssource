import json, os, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "personal_expense_tracker_test.db"
if TEST_DB.exists(): TEST_DB.unlink()
os.environ["DATABASE_PATH"] = str(TEST_DB)
os.environ["APP_NAME"] = "test-app"

import pytest
from fastapi.testclient import TestClient
from app.main import app

EVENTS = []

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def request_json(client):
    def call(method, path, **kwargs):
        started = time.perf_counter()
        start = datetime.now(timezone.utc).isoformat()
        response = getattr(client, method)(path, **kwargs)
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        EVENTS.append({"started_at": start, "finished_at": datetime.now(timezone.utc).isoformat(), "method": method.upper(), "path": path, "status": response.status_code, "response_ms": elapsed, "ok": response.status_code < 400})
        return response
    return call

def pytest_sessionfinish(session, exitstatus):
    report_dir = Path(os.getenv("TEST_REPORT_DIR", "reports"))
    report_dir.mkdir(parents=True, exist_ok=True)
    total = len(EVENTS); passed = sum(e["ok"] for e in EVENTS); times = [e["response_ms"] for e in EVENTS]
    summary = {"started_at": EVENTS[0]["started_at"] if EVENTS else None, "finished_at": datetime.now(timezone.utc).isoformat(), "total_requests": total, "successful_requests": passed, "failed_requests": total - passed, "success_rate_percent": round(passed / total * 100, 2) if total else 0, "average_response_ms": round(sum(times) / len(times), 3) if times else 0, "max_response_ms": max(times) if times else 0, "pytest_exit_code": exitstatus}
    (report_dir / "test-results.json").write_text(json.dumps({"summary": summary, "events": EVENTS}, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = "".join(f"<tr><td>{e['method']}</td><td>{e['path']}</td><td>{e['status']}</td><td>{e['response_ms']}</td><td>{'PASS' if e['ok'] else 'FAIL'}</td></tr>" for e in EVENTS)
    html = f"<html><head><meta charset='utf-8'><title>Expense Tracker Test Report</title><style>body{{font-family:Arial;margin:2rem}}td,th{{padding:.4rem;border:1px solid #ddd}}table{{border-collapse:collapse}}</style></head><body><h1>Expense Tracker Test Report</h1><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre><table><tr><th>Method</th><th>Path</th><th>Status</th><th>ms</th><th>Result</th></tr>{rows}</table></body></html>"
    (report_dir / "test-report.html").write_text(html, encoding="utf-8")
    if TEST_DB.exists(): TEST_DB.unlink()
