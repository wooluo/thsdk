---
name: thsdk
description: |
  Fetch real-time and historical stock market data for Chinese (A-share), US, and Hong Kong markets.
  Trigger when the user asks about stock prices, K-line charts, market indices, sector/industry data,
  order book depth, big order fund flows, intraday data, stock search, or financial news.
  Supports queries like "查询茅台实时价格", "获取苹果股票K线", "上证指数今日行情", "行业板块列表",
  "搜索股票代码", "查看盘口数据", "大单资金流向", "今日新股", "概念板块成分股".
metadata: '{"requires":{"bins":["python3"],"env":["THS_USERNAME","THS_PASSWORD"]}}'
---

# THSDK - Stock Market Data Skill

You have access to thsdk, a Python SDK for fetching stock market data from 同花顺 (THS) via TCP long connections. Use it to retrieve real-time quotes, K-line history, order depth, fund flows, sector listings, and more for Chinese, US, and Hong Kong markets.

## Two Usage Modes

### Mode 1: Direct SDK (preferred for single queries)

```python
from thsdk import THS

ths = THS()
resp = ths.connect()
if not resp.success:
    print("Connection failed:", resp.to_dict())
    # stop here

# ... use ths methods below ...

ths.disconnect()
```

### Mode 2: REST API (preferred for repeated queries or web apps)

If the FastAPI server is running (`cd server && uvicorn main:app`), call these endpoints:

```
GET http://localhost:8000/api/health
GET http://localhost:8000/api/market/{market}?codes=...&query_key=...
GET http://localhost:8000/api/stock/klines?ths_code=...&count=100&interval=day
GET http://localhost:8000/api/stock/intraday?ths_code=...
GET http://localhost:8000/api/stock/depth?ths_code=...
GET http://localhost:8000/api/stock/big-order-flow?ths_code=...
GET http://localhost:8000/api/catalog/{list_type}
GET http://localhost:8000/api/catalog/block-constituents?link_code=...
GET http://localhost:8000/api/search?pattern=...
GET http://localhost:8000/api/news?code=...&market=...
GET http://localhost:8000/api/ipo/today
```

## Market Code Format

All stock codes use THS format with a 4-character market prefix:

| Market | Prefix | Example |
|--------|--------|---------|
| Shanghai A-share | `USHA` | `USHA600519` (贵州茅台) |
| Shenzhen A-share | `USZA` | `USZA300033` (同花顺) |
| Shenzhen A-share | `USZA` | `USZA000001` (平安银行) |
| US stocks | `UNQQ` / `UNQS` | `UNQQTSLA` (Tesla), `UNQSAAPL` (Apple) |
| Hong Kong stocks | `UHKM` / `UHKG` | `UHKM00700` (腾讯), `UHKM09988` (阿里) |
| Shanghai Index | `USHI` | `USHI000001` (上证指数) |
| Shenzhen Index | `USZI` | `USZI399001` (深证成指) |
| Block/Sector | `URFI` | `URFI883404` |
| Futures | `UGFF` | `UGFFIF00` (股指期货) |
| Forex | `UFXB` | `UFXBUSDCNY` |

## Common Tasks

### Search for a stock

```python
resp = ths.search_symbols("贵州茅台")
# Returns list of matches with names, codes, market info
```

### Complete a partial code

```python
resp = ths.complete_ths_code("600519")
# Returns full code like USHA600519
```

### Real-time quote (A-share)

```python
# query_key options: "基础数据", "基础数据2", "基础数据3", "扩展1", "扩展2", "汇总"
resp = ths.market_data_cn("USHA600519", query_key="汇总")
# Key fields: "价格", "涨跌", "涨幅", "名称", "代码", "成交量", "总金额",
#             "昨收价", "开盘价", "最高价", "最低价", "换手率"
```

### Real-time quote (US / HK)

```python
# US stocks - query_key: "基础数据", "每股净资产", "每股收益", "净利润", "财务指标"
resp = ths.market_data_us("UNQQTSLA", query_key="基础数据")

# HK stocks - query_key: "基础数据", "每股净资产", "净利润", "财务指标"
resp = ths.market_data_hk("UHKM00700", query_key="基础数据")
```

### Index data

```python
# query_key: "基础数据", "扩展"
resp = ths.market_data_index("USHI000001", query_key="基础数据")
# 上证指数 real-time data
```

### K-line (candlestick) history

```python
# interval: "1m", "5m", "15m", "30m", "60m", "day", "week", "month"
# adjust: "" (不复权), "前复权", "后复权"
resp = ths.klines("USHA600519", count=100, interval="day", adjust="前复权")
# Each row: "时间", "开盘价", "最高价", "最低价", "价格"(收盘价), "成交量", "成交额"
```

### Intraday tick data

```python
resp = ths.intraday_data("USZA300033")
# Today's minute-by-minute price data
```

### Order book depth (10 levels)

```python
resp = ths.depth("USHA600519")
# Fields: "买1价"..."买10价", "买1量"..."买10量", "卖1价"..."卖10价", "卖1量"..."卖10量"
```

### Big order fund flow

```python
resp = ths.big_order_flow("USHA600519")
# Fields: "大单流入", "大单流出", "主力净量"
```

### Sector / Industry listings

```python
# List all industry sectors
resp = ths.ths_industry()

# List all concept sectors
resp = ths.ths_concept()

# Get constituent stocks of a sector
resp = ths.block_constituents("URFI883404")
# Returns list of stock codes/names in the sector
```

### Stock lists by market

```python
resp = ths.stock_cn_lists()   # All A-share stocks
resp = ths.stock_us_lists()   # All US stocks
resp = ths.stock_hk_lists()   # All HK stocks
resp = ths.index_list()       # All indices
```

### News

```python
resp = ths.news(code="1A0001", market="USHI")
```

### IPO data

```python
resp = ths.ipo_today()   # Stocks listing today
resp = ths.ipo_wait()    # Stocks waiting to list
```

## Batch Queries

For market data, you can pass multiple codes as a list:

```python
resp = ths.market_data_cn(["USHA600519", "USZA300033", "USHA601318"], query_key="基础数据")
```

## Response Format

All responses return a `Response` object with:
- `response.success` — `True` if query succeeded
- `response.data` — list of dicts with Chinese field names
- `response.error` — error message if failed
- `response.to_dict()` — serialize to `{"success": bool, "data": [...], "error": str, "extra": {...}}`

## Important Notes

- Always `connect()` before querying and `disconnect()` when done
- The SDK uses a native C library + TCP connection; connection errors trigger automatic reconnect in the server
- Field names in responses are in Chinese (e.g., "价格" not "price", "涨幅" not "changePct")
- Chinese market convention: red = up (positive), green = down (negative)
- Trading hours: A-share 9:30-15:00 CST, HK 9:30-16:00 HKT, US pre-market 4:00-9:30 / regular 9:30-16:00 / after-hours 16:00-20:00 EST
