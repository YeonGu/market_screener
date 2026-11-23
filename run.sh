#!/bin/sh
# 本地跑一遍：补拉数据 → 重建。需要环境变量 POLYGON_API_KEY 或本目录 .env。
set -e
cd "$(dirname "$0")"
python3 fetch.py
python3 build.py
echo "打开 site/index.html"
