"""SIC 行业码缓存：watchlist/cache/sic.csv  (cik, sic, sic_desc, edgar_name, fetched)

来源 SEC EDGAR submissions 接口 data.sec.gov/submissions/CIK##########.json。
只抓缓存里没有、或抓取超过 MAX_AGE 天的 CIK；限速 8 次/秒（SEC 上限 10）。

抓取失败的 CIK 跳过不写缓存（下次再试）；连续失败 5 次就停，不拖住 build。

    python fetch_sic.py CIK [CIK ...]     # 通常由 build.py 调用
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parent / "cache" / "sic.csv"
UA = "etf-research personal-script research@localhost"   # 与 scripts/pull_edgar 相同的通用 UA
MAX_AGE = 120
RPS = 8.0


def load() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_csv(CACHE, dtype={"cik": str, "sic": str}, na_filter=False)
    return pd.DataFrame(columns=["cik", "sic", "sic_desc", "edgar_name", "fetched"])


def get(cik: str) -> dict | None:
    url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    for k in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
            j = json.loads(b)
            return {"sic": str(j.get("sic") or ""), "sic_desc": j.get("sicDescription") or "",
                    "edgar_name": j.get("name") or ""}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"sic": "", "sic_desc": "", "edgar_name": ""}
            time.sleep(2 ** k)
        except Exception:
            time.sleep(2 ** k)
    return None


def refresh(ciks) -> pd.DataFrame:
    c = load()
    today = date.today()
    age = {r.cik: (today - date.fromisoformat(r.fetched)).days for r in c.itertuples()}
    todo = sorted({str(int(x)) for x in ciks if x} - {k for k, a in age.items() if a <= MAX_AGE})
    rows, t0, fails = [], time.time(), 0
    for i, cik in enumerate(todo):
        t = time.time()
        r = get(cik)
        if r is None:
            fails += 1
            if fails >= 5:
                print(f"WARN: EDGAR 连续失败，剩余 {len(todo) - i - 1} 个 CIK 下次再抓")
                break
            continue
        fails = 0
        rows.append({"cik": cik, **r, "fetched": today.isoformat()})
        time.sleep(max(0.0, 1 / RPS - (time.time() - t)))
        if (i + 1) % 250 == 0:
            print(f"  sic {i + 1}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)
    if rows:
        new = pd.DataFrame(rows)
        c = pd.concat([c[~c.cik.isin(new.cik)], new], ignore_index=True)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        c.sort_values("cik").to_csv(CACHE, index=False)
    print(f"sic: fetched {len(rows)}, cache {len(c)}")
    return c


if __name__ == "__main__":
    refresh(sys.argv[1:])
