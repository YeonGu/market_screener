"""股票关注名单：全市场成交额前 500 ∪ 每个板块成交额前 10。

口径
  宇宙      Polygon reference_tickers 里 type ∈ {CS, ADRC} 且 active 的普通股/ADR（不含 ETF、优先股、权证）
  成交额    最近 20 个交易日 volume × vwap 的中位数（美元）；20 天里至少有 15 天有成交
  板块      SEC EDGAR 的 SIC 码 → boards.py 的细分板块（每个板块对应一个参考 ETF），个别大名字手工改
  价格      Polygon 分组日线（未复权），用 Polygon splits 接口把最近 400 天的拆股调回去；不调股息
  入选      全市场排名 ≤ 500，或板块内排名 ≤ 10（「未归类」板块不参与板块前 10）

输出  site/index.html、site/latest.csv、site/history/（GitHub Pages 发布这个目录）
      history/watchlist_YYYY-MM-DD.csv（进 git；新进/移出对比的是日期更早的最近一份）

    python fetch.py && python build.py
"""
from __future__ import annotations

import glob
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import fetch_sic  # noqa: E402
from boards import BOARDS, SECTORS, board_of  # noqa: E402

DATA = fetch.DATA
SITE = HERE / "site"
HIST = HERE / "history"
TOP_ALL, TOP_BOARD = 500, 10
N_ADV, MIN_ADV_DAYS = 20, 15
N_HIST = 260                 # 52 周高、200 日线、走势图
SIC_FLOOR = 5e6              # 只给成交额 ≥ $5M/天 的名字抓 SIC（候选池）
SPARK = 120


def load_daily() -> pd.DataFrame:
    fs = sorted(glob.glob(str(DATA / "daily/date=*/part.parquet")))[-N_HIST:]
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d["date"] = pd.to_datetime(d.date)
    return d


def adjust_splits(d: pd.DataFrame, s: pd.DataFrame) -> pd.DataFrame:
    s = s[s.ticker.isin(d.ticker.unique()) & (s.execution_date <= d.date.max())]
    for r in s.itertuples():
        m = (d.ticker == r.ticker) & (d.date < r.execution_date)
        f = float(r.split_from) / float(r.split_to)
        d.loc[m, ["open", "high", "low", "close", "vwap"]] *= f
        d.loc[m, "volume"] /= f
    return d


def wide(d, col, cal, cols):
    return d.pivot_table(index="date", columns="ticker", values=col).reindex(index=cal, columns=cols)


def main():
    d = load_daily()
    cal = pd.DatetimeIndex(np.sort(d.date.unique()))
    asof = cal[-1]
    print(f"日线 {cal[0].date()} → {asof.date()}（{len(cal)} 天）")

    ref = pd.read_parquet(DATA / "ref_stocks.parquet")
    ref = ref[ref.type.isin(["CS", "ADRC"]) & ref.active].drop_duplicates("ticker").set_index("ticker")

    last = d[d.date.isin(cal[-N_ADV:])].copy()
    last["dv"] = last.volume * last.vwap.fillna(last.close)
    g = last.groupby("ticker").dv
    adv = g.median()[g.count() >= MIN_ADV_DAYS]
    traded_today = set(d.loc[d.date == asof, "ticker"])
    u = ref.join(adv.rename("adv"), how="inner")
    u = u[u.index.isin(traded_today)].sort_values("adv", ascending=False)
    u["rank_all"] = np.arange(1, len(u) + 1)
    u = u[u.adv >= SIC_FLOOR].copy()

    sic = fetch_sic.refresh(u.cik.dropna().unique()).set_index("cik")
    ck = u.cik.fillna("").map(lambda c: str(int(c)) if c else "")
    u["sic"] = ck.map(sic.sic).fillna("")
    u["sic_desc"] = ck.map(sic.sic_desc).fillna("")
    u["board"] = [board_of(t, s) for t, s in zip(u.index, u.sic)]
    u = u[~u.sic.isin(["6770"])]                     # 空白支票公司（SPAC）
    u["rank_board"] = u.groupby("board").adv.rank(ascending=False, method="first").astype(int)
    pick = (u.rank_all <= TOP_ALL) | ((u.rank_board <= TOP_BOARD) & (u.board != "OTHR"))
    w = u[pick].copy()

    # 价格与指标（拆股调整后）
    tick = sorted(set(w.index) | {v[1] for v in BOARDS.values() if v[1]} | {s[2] for s in SECTORS if s[2]} | {"SPY", "QQQ"})
    dd = adjust_splits(d[d.ticker.isin(tick)].copy(), fetch.splits((asof - timedelta(days=400)).date()))
    C = wide(dd, "close", cal, tick).ffill(limit=3)
    H = wide(dd, "high", cal, tick)

    def ret(k):
        return C.iloc[-1] / C.iloc[-1 - k] - 1

    M = pd.DataFrame({
        "close": C.iloc[-1], "r1": ret(1), "r5": ret(5), "r20": ret(20), "r60": ret(60),
        "off_high": C.iloc[-1] / H.iloc[-252:].max() - 1,
        "vs_ma200": C.iloc[-1] / C.iloc[-200:].mean() - 1,
        "vs_ma50": C.iloc[-1] / C.iloc[-50:].mean() - 1,
    })
    M.loc[C.iloc[-200:].count() < 180, "vs_ma200"] = np.nan
    M.loc[H.iloc[-252:].count() < 240, "off_high"] = np.nan
    w = w.join(M)

    # 和上一期对比：history/ 里日期早于本期的最近一份
    HIST.mkdir(exist_ok=True)
    olds = sorted(p for p in HIST.glob("watchlist_*.csv") if p.stem[10:] < str(asof.date()))
    if olds:
        prev = pd.read_csv(olds[-1], na_filter=False)
        prev_asof = prev["asof"].iloc[0]
        w["new"] = ~w.index.isin(prev.ticker)
        gone = prev[~prev.ticker.isin(w.index)][["ticker", "name", "board"]]
    else:
        prev_asof, gone = "", None
        w["new"] = False

    csv = w.reset_index().rename(columns={"index": "ticker"})
    csv.insert(0, "asof", str(asof.date()))
    csv["prev_asof"] = prev_asof
    csv["board_name"] = csv.board.map(lambda b: BOARDS[b][0])
    cols = ["asof", "ticker", "name", "type", "board", "board_name", "sic", "sic_desc", "adv", "rank_all",
            "rank_board", "close", "r1", "r5", "r20", "r60", "off_high", "vs_ma50", "vs_ma200", "new", "prev_asof"]
    csv = csv[cols].sort_values(["board", "rank_board"])
    csv.to_csv(HIST / f"watchlist_{asof.date()}.csv", index=False)
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(HIST, SITE / "history")
    csv.to_csv(SITE / "latest.csv", index=False)

    # 网页
    etf = M.reindex(sorted({v[1] for v in BOARDS.values() if v[1]} | {s[2] for s in SECTORS if s[2]} | {"SPY", "QQQ"}))
    spark = {t: [None if np.isnan(x) else round(float(x), 4) for x in C[t].iloc[-SPARK:].to_numpy()] for t in w.index}

    def rec(t, r):
        f = lambda x: None if pd.isna(x) else round(float(x), 5)
        return {"t": t, "n": r["name"], "b": r.board, "adv": f(r.adv), "ra": int(r.rank_all), "rb": int(r.rank_board),
                "c": f(r.close), "r1": f(r.r1), "r5": f(r.r5), "r20": f(r.r20), "r60": f(r.r60),
                "hi": f(r.off_high), "m200": f(r.vs_ma200), "m50": f(r.vs_ma50), "new": bool(r.new),
                "sic": r.sic_desc.title(), "sp": spark[t]}

    data = {
        "asof": str(asof.date()), "prev_asof": prev_asof, "built": str(date.today()),
        "rule": {"all": TOP_ALL, "board": TOP_BOARD, "adv_days": N_ADV},
        "sectors": [{"k": k, "n": n, "etf": e} for k, n, e in SECTORS],
        "boards": {k: {"n": v[0], "etf": v[1], "s": v[2]} for k, v in BOARDS.items()},
        "etf": {t: {k: (None if pd.isna(x) else round(float(x), 5)) for k, x in r.items()} for t, r in etf.iterrows()},
        "rows": [rec(t, r) for t, r in w.iterrows()],
        "gone": [] if gone is None else gone.to_dict("records"),
        "n_universe": int(len(ref.join(adv.rename('adv'), how='inner'))),
    }
    html = (HERE / "template.html").read_text().replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    (SITE / "index.html").write_text(html)
    (SITE / ".nojekyll").write_text("")

    n_all = int((w.rank_all <= TOP_ALL).sum())
    print(f"入选 {len(w)}：前 {TOP_ALL} 共 {n_all}，板块前 {TOP_BOARD} 额外 {len(w) - n_all}；"
          f"新进 {int(w.new.sum())}，移出 {0 if gone is None else len(gone)}")
    print(w.groupby("board").size().rename(lambda b: BOARDS[b][0]).sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
