# market_screener · 美股关注名单

**页面：<https://yeongu.github.io/market_screener/>**（GitHub Actions 每个交易日自动更新）

入选规则：全市场成交额前 500 ∪ 每个细分板块成交额前 10（普通股 + ADR）。

| 口径 | |
|---|---|
| 成交额 | 近 20 个交易日 volume × VWAP 的中位数；20 天里至少 15 天有成交 |
| 板块 | SEC EDGAR 的 SIC 码 → 41 个细分板块（各带参考 ETF，如制药 IHE、半导体 SMH）→ 11 大类；`boards.py` 的 `OVERRIDE` 是手工改过的名字 |
| 价格 | Polygon 分组日线（未复权），按 Polygon 拆股记录调整；不调股息 |
| 对比 | 「新进 / 移出」相对上一期；历史名单在缓存里滚动保留 60 期，页面上 `history/` 可翻看 |

## 文件

| 文件 | 作用 |
|---|---|
| `fetch.py` | Polygon 增量日线、代码表、拆股 → `data/`（不进 git） |
| `fetch_sic.py` | SEC EDGAR 的 SIC 码 → `cache/sic.csv`（进 git，120 天过期） |
| `boards.py` | SIC → 板块映射与手工修正 |
| `build.py` | 排名、入选、指标 → `site/`（Pages）+ `data/history/`（滚动 60 期） |
| `template.html` | 页面模板（瑞士国际主义风格） |
| `.github/workflows/update.yml` | 定时：UTC 10:00 周二–周六；也可手动 Run workflow |

## 自动化

- Polygon 密钥只放在仓库 Secret `POLYGON_API_KEY`，代码里只放进 `Authorization` 请求头，不进 URL、日志或产物。
- 原始日线（最近 300 个交易日）和最近 60 期名单都在 Actions cache，约 125 MB；每次运行后只留最新 2 个缓存条目。
- 缓存丢失时自动冷启动重拉约 270 天日线（免费档约 1 小时），上一期名单改从线上 `latest.csv` 取。
- git 里不存历史名单；只有新抓到 SIC 时提交 `cache/sic.csv`。

## 本地运行

```sh
export POLYGON_API_KEY=...      # 或写进本目录 .env（已 gitignore）
sh run.sh                       # = python fetch.py && python build.py，打开 site/index.html
```

改板块：改 `boards.py`（`OVERRIDE` 按代码、`RANGES` 按 SIC 区间），推到 main 会自动重建。
