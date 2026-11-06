import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

def call(url):
    started=time.perf_counter(); result={"started_at":datetime.now(timezone.utc).isoformat(),"url":url}
    try:
        with urlopen(Request(url,headers={"Accept":"application/json"}),timeout=5) as response:
            data=json.loads(response.read()); result.update(finished_at=datetime.now(timezone.utc).isoformat(),status=response.status,response_ms=round((time.perf_counter()-started)*1000,3),version=data.get("version"),valid=all(k in data for k in ("total_income","total_expense","balance")),ok=response.status==200,error=None)
    except Exception as exc: result.update(finished_at=datetime.now(timezone.utc).isoformat(),status=None,response_ms=round((time.perf_counter()-started)*1000,3),version=None,valid=False,ok=False,error=str(exc))
    return result

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--url",default="http://127.0.0.1:8000/api/summary"); p.add_argument("--seconds",type=int,default=90); p.add_argument("--output",default="reports/zero-downtime.json"); a=p.parse_args(); rows=[]; start=time.time()
    while time.time()-start<a.seconds: rows.append(call(a.url)); time.sleep(1)
    groups={"before":rows[:len(rows)//3],"during":rows[len(rows)//3:2*len(rows)//3],"after":rows[2*len(rows)//3:]}; summary={p:{"ok":sum(x["ok"] for x in xs),"total":len(xs),"success_rate":round(sum(x["ok"] for x in xs)/len(xs)*100,2) if xs else 0} for p,xs in groups.items()}; out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({"summary":summary,"requests":rows},ensure_ascii=False,indent=2),encoding="utf-8"); out.with_suffix(".html").write_text("<h1>Personal Expense Tracker Deployment Verification</h1><pre>"+json.dumps(summary,ensure_ascii=False,indent=2)+"</pre>",encoding="utf-8")
