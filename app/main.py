import os, sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "expenses.db")))
DB.parent.mkdir(parents=True, exist_ok=True)
app = FastAPI(title=os.getenv("APP_NAME", "나의 가계부"))

@app.get("/health")
def health():
    with closing(conn()) as c:
        c.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "ok"}

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL CHECK(type IN ('income','expense')),
      date TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount > 0), category TEXT NOT NULL, memo TEXT DEFAULT '')""")
    c.commit(); return c

class TransactionIn(BaseModel):
    type: Literal["income", "expense"]
    date: date
    amount: int = Field(gt=0)
    category: str = Field(min_length=1, max_length=40)
    memo: str = Field(default="", max_length=200)
    @field_validator("category")
    @classmethod
    def category_text(cls, v):
        if not v.strip(): raise ValueError("카테고리를 입력해 주세요.")
        return v.strip()

def row(r): return dict(r)

@app.get("/api/transactions")
def transactions(start: str|None=None, end: str|None=None, category: str|None=None, type: str|None=None):
    sql="SELECT * FROM transactions WHERE 1=1"; args=[]
    for col, val, op in [("date",start,">="),("date",end,"<="),("category",category,"="),("type",type,"=")]:
        if val: sql += f" AND {col} {op} ?"; args.append(val)
    sql += " ORDER BY date DESC, id DESC"
    with closing(conn()) as c: return [row(x) for x in c.execute(sql,args)]

@app.post("/api/transactions", status_code=201)
def create(item: TransactionIn):
    try:
        with closing(conn()) as c:
            cur=c.execute("INSERT INTO transactions(type,date,amount,category,memo) VALUES(?,?,?,?,?)", (item.type,item.date.isoformat(),item.amount,item.category,item.memo.strip())); c.commit()
            return row(c.execute("SELECT * FROM transactions WHERE id=?",(cur.lastrowid,)).fetchone())
    except sqlite3.Error as e: raise HTTPException(500, f"데이터 저장 중 오류가 발생했습니다: {e}")

@app.put("/api/transactions/{tid}")
def update(tid:int, item:TransactionIn):
    with closing(conn()) as c:
        cur=c.execute("UPDATE transactions SET type=?,date=?,amount=?,category=?,memo=? WHERE id=?",(item.type,item.date.isoformat(),item.amount,item.category,item.memo.strip(),tid)); c.commit()
        if not cur.rowcount: raise HTTPException(404,"거래 내역을 찾을 수 없습니다.")
        return row(c.execute("SELECT * FROM transactions WHERE id=?",(tid,)).fetchone())

@app.delete("/api/transactions/{tid}")
def delete(tid:int):
    with closing(conn()) as c:
        cur=c.execute("DELETE FROM transactions WHERE id=?",(tid,)); c.commit()
        if not cur.rowcount: raise HTTPException(404,"거래 내역을 찾을 수 없습니다.")
    return {"ok":True}

@app.get("/api/summary")
def summary():
    month=date.today().isoformat()[:7]
    with closing(conn()) as c:
        total=c.execute("SELECT type,COALESCE(SUM(amount),0) n FROM transactions GROUP BY type").fetchall()
        this=c.execute("SELECT type,COALESCE(SUM(amount),0) n FROM transactions WHERE substr(date,1,7)=? GROUP BY type",(month,)).fetchall()
        cats=c.execute("SELECT category,SUM(amount) amount FROM transactions WHERE type='expense' GROUP BY category ORDER BY amount DESC").fetchall()
        months=c.execute("SELECT substr(date,1,7) month,type,SUM(amount) amount FROM transactions GROUP BY month,type ORDER BY month").fetchall()
    def vals(rs): return {r['type']:r['n'] for r in rs}
    t=vals(total); m=vals(this)
    return {"total_income":t.get('income',0),"total_expense":t.get('expense',0),"balance":t.get('income',0)-t.get('expense',0),"month_income":m.get('income',0),"month_expense":m.get('expense',0),"categories":[dict(x) for x in cats],"months":[dict(x) for x in months]}

app.mount("/static", StaticFiles(directory=ROOT/"static"), name="static")
@app.get("/")
def index(): return FileResponse(ROOT/"static"/"index.html")

