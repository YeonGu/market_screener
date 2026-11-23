"""Polygon 数据：增量日线、股票代码表、拆股。全部写在 data/（不进 git；CI 里放 Actions cache）。

  data/daily/date=YYYY-MM-DD/part.parquet   分组日线（未复权），保留最近 KEEP 个交易日
  data/empty_dates.json                     已确认无数据的日期（周末以外的休市日）
  data/ref_stocks.parquet                   普通股 + ADR 代码表，超过 REF_MAX_AGE 天刷新
  data/splits.csv                           最近 400 天的拆股，当天有效

密钥只从环境变量 POLYGON_API_KEY（或本目录 .env）读，只放在 Authorization 请求头里，
不拼进 URL、不打印、不写进任何异常信息。

    python fetch.py          # 免费档 5 次/分钟；冷启动约 270 次调用 ≈ 1 小时，之后每天 1–3 次
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
DATA = Path(os.getenv("MS_DATA", HERE / "data"))
API = "https://api.polygon.io"
KEEP = 300            # 保留的交易日数（build 用 260）
COLD_DAYS = 390       # 冷启动回看的日历天数（≈ 268 个交易日）
REF_MAX_AGE = 7
MIN_INTERVAL = float(os.getenv("POLYGON_MIN_INTERVAL", "12.5"))   # 免费档 5 次/分钟

SCHEMA = pa.schema([("date", pa.date32()), ("ticker", pa.string()), ("open", pa.float64()),
                    ("high", pa.float64()), ("low", pa.float64()), ("close", pa.float64()),
                    ("volume", pa.float64()), ("vwap", pa.float64()), ("transactions", pa.int64())])


def _key() -> str:
    k = os.getenv("POLYGON_API_KEY")
    if not k and (HERE / ".env").exists():
        for line in (HERE / ".env").read_text().splitlines():
            if line.strip().startswith("POLYGON_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        raise SystemExit("缺少 POLYGON_API_KEY（环境变量或 .env）")
    return k


_last = [0.0]


def get(url: str) -> dict:
    """GET JSON。url 不含密钥；报错信息只带路径，不带查询串。"""
    if not url.startswith("http"):
        url = API + url
    path = url.split("?")[0].replace(API, "")
    for k in range(6):
        wait = MIN_INTERVAL - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_key()}",
                                                   "User-Agent": "market-screener"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (429, 500, 502, 503, 504):
                time.sleep(15 * (k + 1))
                continue
            raise RuntimeError(f"Polygon {path}: HTTP {code}") from None
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (k + 1))
    raise RuntimeError(f"Polygon {path}: 重试仍失败")


def ny_today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()


# ---------------------------------------------------------------- 日线
def have_dates() -> list[date]:
    return sorted(date.fromisoformat(p.name[5:]) for p in (DATA / "daily").glob("date=*") if (p / "part.parquet").exists())


def update_daily():
    DATA.mkdir(parents=True, exist_ok=True)
    ef = DATA / "empty_dates.json"
    empty = set(json.loads(ef.read_text())) if ef.exists() else set()
    have = have_dates()
    end = ny_today() - timedelta(days=1)              # 前一个纽约日历日一定已收完
    start = have[-1] + timedelta(days=1) if have else end - timedelta(days=COLD_DAYS)
    todo = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    todo = [d for d in todo if d.weekday() < 5 and d.isoformat() not in empty]
    print(f"日线：已有 {len(have)} 天（{have[0] if have else '-'} → {have[-1] if have else '-'}），待拉 {len(todo)} 天", flush=True)
    for i, d in enumerate(todo):
        j = get(f"/v2/aggs/grouped/locale/us/market/stocks/{d.isoformat()}?adjusted=false")
        res = j.get("results") or []
        if not res:
            if (end - d).days >= 4:                    # 足够久之前仍为空 → 休市
                empty.add(d.isoformat())
                ef.write_text(json.dumps(sorted(empty)))
            print(f"  {d} 空", flush=True)
            continue
        df = pd.DataFrame(res)
        out = pd.DataFrame({
            "date": d, "ticker": df["T"], "open": df.get("o"), "high": df.get("h"), "low": df.get("l"),
            "close": df.get("c"), "volume": df.get("v"), "vwap": df.get("vw"),
            "transactions": df.get("n", pd.Series(dtype="float")).fillna(0).astype("int64")})
        p = DATA / "daily" / f"date={d.isoformat()}"
        p.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pandas(out, schema=SCHEMA, preserve_index=False), p / "part.parquet")
        if (i + 1) % 20 == 0 or i == len(todo) - 1:
            print(f"  {i + 1}/{len(todo)}  {d}  {len(out)} 行", flush=True)
    have = have_dates()
    for d in have[:-KEEP]:                              # 只留最近 KEEP 天
        (DATA / "daily" / f"date={d.isoformat()}" / "part.parquet").unlink()
        (DATA / "daily" / f"date={d.isoformat()}").rmdir()


# ---------------------------------------------------------------- 代码表
def update_reference(force=False):
    f = DATA / "ref_stocks.parquet"
    if f.exists() and not force and (time.time() - f.stat().st_mtime) < REF_MAX_AGE * 86400:
        return
    rows = []
    for typ in ("CS", "ADRC"):
        url = f"/v3/reference/tickers?market=stocks&type={typ}&active=true&limit=1000"
        while url:
            j = get(url)
            rows += [{"ticker": r.get("ticker"), "name": r.get("name"), "type": r.get("type"),
                      "active": bool(r.get("active")), "cik": r.get("cik")} for r in j.get("results", [])]
            url = j.get("next_url")
    df = pd.DataFrame(rows).drop_duplicates("ticker")
    if len(df) < 3000:
        raise RuntimeError(f"代码表只有 {len(df)} 行，不覆盖旧表")
    df.to_parquet(f, index=False)
    print(f"代码表：{len(df)} 只（{df.type.value_counts().to_dict()}）", flush=True)


# ---------------------------------------------------------------- 拆股
def splits(since: date) -> pd.DataFrame:
    f = DATA / "splits.csv"
    if f.exists() and date.fromtimestamp(f.stat().st_mtime) == date.today():
        return pd.read_csv(f, na_filter=False, parse_dates=["execution_date"])
    url, rows = f"/v3/reference/splits?execution_date.gte={since}&limit=1000", []
    while url:
        j = get(url)
        rows += j.get("results", [])
        url = j.get("next_url")
    s = pd.DataFrame(rows, columns=["ticker", "execution_date", "split_from", "split_to"])
    s["execution_date"] = pd.to_datetime(s.execution_date)
    s.to_csv(f, index=False)
    return s


if __name__ == "__main__":
    update_reference()
    update_daily()
