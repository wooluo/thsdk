# THSDK 股票行情网站 — 完整说明文档

本文档详细描述 `server/`（FastAPI 后端）和 `web/`（Vercel 静态前端）的架构设计、API 接口、前端页面、部署方式与二次开发指南。

---

## 目录

- [1. 架构概览](#1-架构概览)
- [2. 项目结构](#2-项目结构)
- [3. 后端 (server/)](#3-后端-server)
  - [3.1 连接管理](#31-连接管理)
  - [3.2 环境变量](#32-环境变量)
  - [3.3 API 接口完整列表](#33-api-接口完整列表)
  - [3.4 统一响应格式](#34-统一响应格式)
  - [3.5 错误处理](#35-错误处理)
- [4. 前端 (web/)](#4-前端-web)
  - [4.1 技术栈](#41-技术栈)
  - [4.2 路由设计](#42-路由设计)
  - [4.3 页面详细说明](#43-页面详细说明)
  - [4.4 数据字段映射](#44-数据字段映射)
  - [4.5 API 客户端配置](#45-api-客户端配置)
  - [4.6 工具函数](#46-工具函数)
- [5. 本地开发](#5-本地开发)
- [6. 部署指南](#6-部署指南)
  - [6.1 后端部署](#61-后端部署)
  - [6.2 前端部署 (Vercel)](#62-前端部署-vercel)
  - [6.3 跨域配置](#63-跨域配置)
- [7. 二次开发指南](#7-二次开发指南)
  - [7.1 新增后端 API 端点](#71-新增后端-api-端点)
  - [7.2 新增前端页面](#72-新增前端页面)
  - [7.3 新增市场支持](#73-新增市场支持)

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────┐
│                  用户浏览器                           │
│         Vercel / 本地静态服务 (port 3000)             │
│                                                     │
│  index.html ──> router.js ──> pages/*.js            │
│       │              │                              │
│       └── api.js ────┴──> HTTP GET 请求             │
└────────────────────────┬────────────────────────────┘
                         │  REST API (JSON)
                         ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI 后端 (port 8000)                │
│                                                     │
│  main.py                                            │
│    ├── routes/market.py   ──> ths.market_data_*()   │
│    ├── routes/stock.py    ──> ths.klines() 等       │
│    ├── routes/catalog.py  ──> ths.ths_industry() 等 │
│    └── routes/misc.py     ──> ths.search_symbols()  │
│                                                     │
│  connection.py (THSSingletonConnection)              │
│    └── 单例 THS 客户端 + RLock + 自动重连            │
│                                                     │
│  thsdk (Python SDK) ──> C 动态库 ──> TCP 长连接      │
└─────────────────────────────────────────────────────┘
```

核心设计思路：

- **分离部署**：后端需要原生 C 库支持，跑在 VPS/Railway 上；前端是纯静态文件，跑在 Vercel CDN 上
- **单连接复用**：后端通过 `THSSingletonConnection` 维护一条 TCP 长连接，所有 HTTP 请求排队复用，自动断线重连
- **无构建步骤**：前端使用原生 JavaScript ES Modules，不依赖 Node.js 构建工具链，直接部署
- **字段自动翻译**：thsdk 的 `Response` 类在解析 JSON 时，自动将数字字段 ID 映射为中文名称（如 `10` → `"价格"`、`199112` → `"涨幅"`），前端直接使用中文字段名

---

## 2. 项目结构

```
thsdk/
├── server/                         # FastAPI 后端
│   ├── main.py                     # 应用入口、CORS、路由注册、生命周期
│   ├── config.py                   # 环境变量配置
│   ├── connection.py               # THSSingletonConnection 单例连接管理
│   ├── schemas.py                  # 请求参数模型（备用）
│   ├── requirements.txt            # Python 依赖
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── market.py               # 市场行情接口（cn/us/hk/index/block/future/forex）
│       ├── stock.py                # 个股详情接口（K线/分时/盘口/大单/竞价）
│       ├── catalog.py              # 板块/列表接口（行业/概念/股票列表/成分股）
│       └── misc.py                 # 搜索/新闻/IPO等杂项接口
│
├── web/                            # 静态前端
│   ├── vercel.json                 # Vercel 部署配置（SPA rewrite）
│   ├── index.html                  # 入口 HTML
│   ├── css/
│   │   └── style.css               # 暗色主题样式（红涨绿跌）
│   ├── js/
│   │   ├── api.js                  # 后端 API 客户端封装
│   │   ├── utils.js                # 格式化工具函数与常量
│   │   └── router.js               # Hash 路由 + 导航搜索
│   └── pages/
│       ├── overview.js             # 市场总览页（指数卡片 + 涨跌榜）
│       ├── detail.js               # 个股详情页（K线图 + 盘口 + 资金流）
│       ├── search.js               # 搜索页（防抖搜索 + 结果列表）
│       └── sectors.js              # 板块页（行业/概念 + 成分股）
│
├── WEB_APP.md                      # 本文档
└── README.md                       # thsdk SDK 主文档
```

---

## 3. 后端 (server/)

### 3.1 连接管理

**文件**: `server/connection.py`

`THSSingletonConnection` 是整个后端的核心组件，负责：

| 特性 | 说明 |
|------|------|
| **单例连接** | 全局只有一个 `THS` 客户端实例，所有 HTTP 请求共享 |
| **线程安全** | 使用 `threading.RLock` 序列化所有 SDK 调用，防止并发冲突 |
| **懒连接** | 首次请求时才建立 TCP 连接，不是启动时 |
| **自动重连** | 检测到连接错误（"未登录"、"断开"、"socket"等关键词）时自动重置并重试一次 |
| **优雅关闭** | FastAPI shutdown 事件中调用 `connection.close()` 断开连接 |

```python
# connection.py 核心流程
class THSSingletonConnection:
    def execute(self, query):
        with self._lock:                          # 获取锁
            ths = self._ensure_connected()         # 确保 TCP 连接存活
            result = query(ths)                    # 执行 SDK 查询
            if self._should_reconnect(result):     # 检测到连接断开
                self._reset()                      # 断开旧连接
                ths = self._ensure_connected()     # 重新连接
                result = query(ths)                # 重试查询
            return result
```

**连接错误检测**（`_is_connection_error`）：检查错误信息中是否包含以下关键词：

- `未登录`、`连接`、`断开`（中文）
- `disconnect`、`socket`、`tcp`、`broken pipe`、`connection reset`、`reset by peer`（英文）

### 3.2 环境变量

**文件**: `server/config.py`

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_HOST` | `0.0.0.0` | 监听地址 |
| `API_PORT` | `8000` | 监听端口 |
| `CORS_ORIGINS` | `*` | 允许的跨域来源，逗号分隔。生产环境应设为前端域名 |

此外，thsdk 自身支持的环境变量也会生效：

| 变量 | 说明 |
|------|------|
| `THS_USERNAME` | 同花顺账户用户名 |
| `THS_PASSWORD` | 同花顺账户密码 |
| `THS_MAC` | MAC 地址 |

若未设置账户信息，SDK 将自动使用临时游客账户（权限有限）。

### 3.3 API 接口完整列表

所有接口均为 **HTTP GET**，参数通过 **Query String** 传递，返回 **JSON**。

#### 健康检查

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/health` | 无 | 返回 `{"status": "ok"}` |

#### 市场行情 (`routes/market.py`)

所有市场行情接口共用 `/{market}` 路径，通过 URL 路径区分市场：

| 方法 | 路径 | 映射到 SDK 方法 |
|------|------|-----------------|
| GET | `/api/market/cn` | `ths.market_data_cn()` |
| GET | `/api/market/us` | `ths.market_data_us()` |
| GET | `/api/market/hk` | `ths.market_data_hk()` |
| GET | `/api/market/index` | `ths.market_data_index()` |
| GET | `/api/market/block` | `ths.market_data_block()` |
| GET | `/api/market/future` | `ths.market_data_future()` |
| GET | `/api/market/forex` | `ths.market_data_forex()` |

**通用参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `codes` | string | 是 | — | 逗号分隔的证券代码，如 `USHA600519,USHA601318` |
| `query_key` | string | 否 | `基础数据` | 查询配置键名 |

**请求示例**：

```
GET /api/market/cn?codes=USZA300033,USHA600519&query_key=基础数据
GET /api/market/us?codes=UNQQTSLA&query_key=基础数据
GET /api/market/index?codes=USHI000001,USZI399001&query_key=基础数据
GET /api/market/block?codes=URFI883404&query_key=基础数据
```

**query_key 可选值**（不同市场支持的键名不同，详见 `src/thsdk/query_configs.py`）：

| 市场 | query_key | 包含字段 |
|------|-----------|----------|
| cn | `基础数据` | 代码、名称、价格、涨速、成交量、当前量、开盘价、昨收价、最高价、最低价、总金额、交易笔数、成交方向 |
| cn | `基础数据2` | 代码、名称、价格、涨速、当前量、成交量、总金额、昨收价、成交方向 |
| cn | `扩展1` | 涨幅、主力净量、主力净流入、涨跌、换手率、振幅、量比、市盈率TTM、市净率 |
| cn | `扩展2` | 涨幅、涨跌、主力净量、主力净流入、换手率、总市值、委比、量比、市盈率TTM、流通市值 |
| cn | `汇总` | 综合基础+扩展大量字段 |
| us | `基础数据` | 代码、名称、价格、开盘价、昨收价、最高价、最低价、成交量等 |
| hk | `基础数据` | 代码、名称、价格、成交量、总金额、昨收价、开盘价、最高价、最低价 |
| index | `基础数据` | 代码、名称、价格、成交量、当前量、开盘价、最高价、最低价、总金额、昨收价 |
| block | `基础数据` | 名称、上涨家数、下跌家数、成交量、总金额、板块总市值、代码、领涨股、涨停家数、跌停家数 |

#### 个股详情 (`routes/stock.py`)

| 方法 | 路径 | 映射到 SDK 方法 |
|------|------|-----------------|
| GET | `/api/stock/klines` | `ths.klines()` |
| GET | `/api/stock/intraday` | `ths.intraday_data()` |
| GET | `/api/stock/depth` | `ths.depth()` |
| GET | `/api/stock/big-order-flow` | `ths.big_order_flow()` |
| GET | `/api/stock/call-auction` | `ths.call_auction()` |

**K线接口参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ths_code` | string | 是 | — | 证券代码，如 `USZA300033` |
| `count` | int | 否 | `100` | K线条数 |
| `interval` | string | 否 | `day` | K线周期：`1m`/`5m`/`15m`/`30m`/`60m`/`120m`/`day`/`week`/`month`/`quarter`/`year` |
| `adjust` | string | 否 | `""` | 复权方式：`""`（不复权）/ `forward`（前复权）/ `backward`（后复权） |

```
GET /api/stock/klines?ths_code=USZA300033&count=100&interval=day&adjust=
GET /api/stock/klines?ths_code=USZA300033&count=50&interval=5m
GET /api/stock/klines?ths_code=USZA300033&count=200&interval=week&adjust=forward
```

**其他接口参数**：

| 路径 | 参数 | 说明 |
|------|------|------|
| `/api/stock/intraday` | `ths_code` | 当日分时数据 |
| `/api/stock/depth` | `ths_code` | 5档/10档买卖盘口 |
| `/api/stock/big-order-flow` | `ths_code` | 大单资金流（仅A股） |
| `/api/stock/call-auction` | `ths_code` | 集合竞价数据 |

#### 板块与列表 (`routes/catalog.py`)

| 方法 | 路径 | 映射到 SDK 方法 | 说明 |
|------|------|-----------------|------|
| GET | `/api/catalog/industry` | `ths.ths_industry()` | 同花顺行业板块列表 |
| GET | `/api/catalog/concept` | `ths.ths_concept()` | 同花顺概念板块列表 |
| GET | `/api/catalog/stock-cn` | `ths.stock_cn_lists()` | 沪深A股列表 |
| GET | `/api/catalog/stock-us` | `ths.stock_us_lists()` | 美股列表 |
| GET | `/api/catalog/stock-hk` | `ths.stock_hk_lists()` | 港股列表 |
| GET | `/api/catalog/index-list` | `ths.index_list()` | 指数列表 |
| GET | `/api/catalog/block-constituents` | `ths.block_constituents()` | 板块成分股 |

列表类接口无需额外参数，直接 GET 即可。

成分股接口参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `link_code` | string | 是 | 板块代码，如 `URFI883404` |

```
GET /api/catalog/industry
GET /api/catalog/concept
GET /api/catalog/block-constituents?link_code=URFI883404
```

#### 搜索与杂项 (`routes/misc.py`)

| 方法 | 路径 | 映射到 SDK 方法 | 说明 |
|------|------|-----------------|------|
| GET | `/api/search` | `ths.search_symbols()` | 证券模糊搜索 |
| GET | `/api/complete-code` | `ths.complete_ths_code()` | 代码补全 |
| GET | `/api/news` | `ths.news()` | 资讯列表 |
| GET | `/api/ipo/today` | `ths.ipo_today()` | 今日IPO |

**参数**：

| 路径 | 参数 | 说明 |
|------|------|------|
| `/api/search` | `pattern`（必填）| 搜索关键词，如 `同花顺`、`300033` |
| `/api/complete-code` | `ths_code`（必填）| 纯数字代码，如 `300033` |
| `/api/news` | `code`（默认 `1A0001`）、`market`（默认 `USHI`）| 资讯过滤条件 |
| `/api/ipo/today` | 无 | 今日新股 |

```
GET /api/search?pattern=同花顺
GET /api/complete-code?ths_code=300033
GET /api/news?code=1A0001&market=USHI
GET /api/ipo/today
```

### 3.4 统一响应格式

所有 API 接口返回统一的 JSON 结构：

```json
{
    "success": true,
    "error": "",
    "data": [ ... ],
    "extra": { ... },
    "timing": {
        "sdk_duration_ms": 123.45,
        "lock_wait_ms": 0.12,
        "connect_duration_ms": 0
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 请求是否成功 |
| `error` | string | 错误信息，成功时为空字符串 |
| `data` | array/dict/null | 主要数据。市场行情和K线为数组，每项是一个证券的数据字典 |
| `extra` | dict | 附加信息，如 `ServerDelay`、`代码`、`total_count` 等 |
| `timing` | dict | 性能计时信息（后端注入，非 SDK 返回） |

**data 中每个字典的字段名**是中文（由 thsdk `Response` 类自动从数字 ID 翻译），例如：

```json
{
    "代码": "USZA300033",
    "名称": "同花顺",
    "价格": 317.8,
    "涨跌": -0.38,
    "涨幅": -0.12,
    "昨收价": 318.18,
    "开盘价": 317.98,
    "最高价": 318.74,
    "最低价": 312.38,
    "成交量": 5734581,
    "总金额": 1809545100,
    "换手率": 10.64,
    "市盈率TTM": 45.23,
    "总市值": 170892000000
}
```

### 3.5 错误处理

后端对每个端点都做了 try-except 包裹，确保不会抛出 500 错误。错误响应格式：

```json
{
    "success": false,
    "error": "具体错误信息",
    "data": null
}
```

常见错误场景：

| 错误信息 | 原因 | 解决方式 |
|----------|------|----------|
| `不支持的市场: xxx` | URL 路径中的市场标识无效 | 使用 cn/us/hk/index/block/future/forex |
| `不支持的列表类型: xxx` | catalog 路径中的类型无效 | 使用 industry/concept/stock-cn/stock-us/stock-hk/index-list |
| `THS 连接失败` | TCP 连接建立失败 | 检查网络、账户信息 |
| SDK 原始错误 | 代码格式不对、权限不足等 | 检查 ths_code 格式、账户权限 |

---

## 4. 前端 (web/)

### 4.1 技术栈

| 技术 | 用途 | 说明 |
|------|------|------|
| 原生 JavaScript (ES Modules) | 所有逻辑 | 无框架、无编译步骤 |
| TradingView Lightweight Charts | K线/分时图 | 唯一外部依赖，CDN 引入 |
| Hash 路由 | SPA 导航 | `#/`、`#/stock/xxx`、`#/search`、`#/sectors` |
| CSS Custom Properties | 暗色主题 | 红涨绿跌（中国市场惯例） |

### 4.2 路由设计

**文件**: `web/js/router.js`

| Hash 路径 | 页面文件 | 说明 |
|-----------|----------|------|
| `#/` | `pages/overview.js` | 市场总览（默认页） |
| `#/stock/{ths_code}` | `pages/detail.js` | 个股详情，如 `#/stock/USZA300033` |
| `#/search` | `pages/search.js` | 搜索页，支持 `?q=关键词` 参数 |
| `#/sectors` | `pages/sectors.js` | 板块页 |

路由监听 `window.hashchange` 事件，匹配正则后调用对应页面的 `render` 函数。导航栏搜索框按回车跳转到 `#/search?q=...`。

### 4.3 页面详细说明

#### 市场总览 (`pages/overview.js`)

**路由**: `#/`

**布局**:

```
┌──────────────────────────────────────────────────┐
│  主要指数                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │上证指数│ │深证成指│ │创业板指│ │恒生指数│ │纳斯达克│   │
│  │3241.52│ │10456 │ │2089  │ │22100 │ │17800 │   │
│  │+0.53% │ │-0.21%│ │+1.12%│ │-0.45%│ │+0.89%│   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                                    │
│  ┌─── A股涨幅榜 Top 20 ──┐ ┌─── A股跌幅榜 Top 20 ──┐ │
│  │ 名称 代码 价格 涨幅 额 │ │ 名称 代码 价格 涨幅 额 │ │
│  │ ...                    │ │ ...                    │ │
│  └────────────────────────┘ └────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**功能**:
- 顶部 5 个指数卡片：上证指数、深证成指、创业板指、恒生指数、纳斯达克
- 中部两列：涨幅榜/跌幅榜各 Top 20
- 每 **5 秒** 自动刷新所有数据
- 点击任何股票行跳转到详情页

**数据加载流程**:
1. 调用 `/api/market/index?codes=USHI000001,USZI399001,...` 获取指数数据
2. 调用 `/api/catalog/stock-cn` 获取A股代码列表
3. 取前 50 个代码，调用 `/api/market/cn?codes=...&query_key=扩展2` 获取行情
4. 按"涨幅"字段排序，取前 20 和后 20

**跟踪的指数代码**（定义在 `utils.js` 的 `INDEX_CODES`）：

| 指数名称 | THS 代码 |
|----------|----------|
| 上证指数 | `USHI000001` |
| 深证成指 | `USZI399001` |
| 创业板指 | `USZI399006` |
| 恒生指数 | `UHKMHSI` |
| 纳斯达克 | `UNQQIXIC` |

#### 个股详情 (`pages/detail.js`)

**路由**: `#/stock/{ths_code}`

**布局**:

```
┌──────────────────────────────────────────────────┐
│  同花顺  USZA300033  317.80  -0.38 (-0.12%)      │
│  开盘:317.98  最高:318.74  最低:312.38  昨收:318.18│
│  成交量:573万  成交额:18.10亿  换手率:10.64%      │
│                                                    │
│  [分时][1分][5分][15分][30分][60分][日K][周K][月K] │
│  ┌──────────────────────────────────────────────┐ │
│  │                                              │ │
│  │          TradingView K线图 / 分时图           │ │
│  │                                              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌─── 买卖盘口 ──────┐  ┌─── 大单资金流 ──────┐  │
│  │ 卖10 318.50  200  │  │ 主力净流入  -2.34亿  │  │
│  │ ...               │  │ 主力净量   -1.23%    │  │
│  │ 卖1  317.81 1700  │  │ ▓▓░░░░░░░ 流入/流出  │  │
│  │ ──────────────── │  │ 流入 18.5亿  流出 20.8亿│  │
│  │ 买1  317.80 12237 │  │                      │  │
│  │ ...               │  │                      │  │
│  │ 买10 317.60  300  │  │                      │  │
│  └───────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**功能**:
- 头部实时报价：根据 ths_code 前缀自动判断市场（A/港/美/指数）
- K线图：支持 9 种周期切换（分时、1分、5分、15分、30分、60分、日、周、月）
- K线图使用 TradingView Lightweight Charts，暗色主题，红涨绿跌蜡烛
- K线图下方附带成交量柱状图
- 分时图模式切换为折线图
- 10 档买卖盘口
- 大单资金流：净流入/流出、主力净量、可视化柱条
- 报价每 **5 秒** 自动刷新

**K线图渲染**:

- 日/周/月 K 线使用 `candlestick` series，红涨绿跌
- 分钟 K 线同样使用 `candlestick` series
- 分时模式使用 `line` series（蓝色折线）
- 成交量使用底部 `histogram` series
- 图表自动适应容器宽度（`ResizeObserver`）

**市场自动识别**（根据 ths_code 前 4 位）：

| 前缀 | 调用接口 |
|------|----------|
| `USHA`/`USZA`/`USHB`/`USZB`/`USTM` | `marketCN` |
| `UNQQ`/`UNQS` | `marketUS` |
| `UHKM`/`UHKG` | `marketHK` |
| `USHI`/`USZI` | `marketIndex` |

#### 搜索页 (`pages/search.js`)

**路由**: `#/search`（支持 `?q=关键词` 参数）

**功能**:
- 单输入框，**300ms 防抖**搜索
- 调用 `/api/search?pattern=xxx`
- 展示搜索结果列表：名称、THSCODE、市场
- 点击结果跳转到 `#/stock/{thscode}`
- 支持 URL 参数预填充搜索词：`#/search?q=同花顺`

#### 板块页 (`pages/sectors.js`)

**路由**: `#/sectors`

**布局**:

```
┌──────────────────────────────────────────────────┐
│  [行业板块]  [概念板块]                            │
│                                                    │
│  ┌── 板块列表 ──┐  ┌── 成分股表格 ──────────────┐ │
│  │ 白酒   +2.3% │  │ 名称  代码  价格  涨幅  量  │ │
│  │ 半导体 +1.8% │  │ 贵州茅台 USHA600519 ...    │ │
│  │ ...          │  │ 五粮液   USZA000858 ...    │ │
│  │ 选中项高亮    │  │ ...                       │ │
│  └──────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**功能**:
- 顶部 Tab 切换：行业板块 / 概念板块
- 左侧板块列表，按涨幅降序排列
- 点击板块加载成分股 + 实时价格
- 成分股按涨幅降序排列
- 点击成分股跳转到详情页
- 板块列表数据来源于 `ths_industry()`/`ths_concept()`，成分股来源于 `block_constituents()`

**成分股价格获取**:
1. 调用 `/api/catalog/block-constituents?link_code=xxx` 获取成分股代码列表
2. 每批 50 个代码，调用 `/api/market/cn?codes=...&query_key=扩展2` 获取价格
3. 合并所有批次，按涨幅排序

### 4.4 数据字段映射

thsdk SDK 通过 `Response._convert_item()` 将原始数字字段 ID 翻译为中文字段名。前端直接使用这些中文名称访问数据。

**常用字段对照表**（完整列表见 `src/thsdk/_constants.py` 中的 `FieldNameMap`）：

| 数字 ID | 中文名称 | 说明 |
|---------|----------|------|
| 1 | 时间 | 时间戳/时间 |
| 5 | 代码 | 证券代码（如 USZA300033） |
| 6 | 昨收价 | 昨日收盘价 |
| 7 | 开盘价 | 开盘价 |
| 8 | 最高价 | 最高价 |
| 9 | 最低价 | 最低价 |
| 10 | 价格 | 当前价格 |
| 13 | 成交量 | 成交量（股/手） |
| 19 | 总金额 | 成交金额 |
| 55 | 名称 | 证券名称 |
| 199112 | 涨幅 | 涨跌幅百分比 |
| 264648 | 涨跌 | 涨跌额 |
| 1968584 | 换手率 | 换手率百分比 |
| 1771976 | 量比 | 量比 |
| 3153 | 市盈率TTM | 滚动市盈率 |
| 2947 | 市净率 | 市净率 |
| 3541450 | 总市值 | 总市值 |
| 3475914 | 流通市值 | 流通市值 |
| 592888 | 主力净量 | 主力净流入占比 |
| 592890 | 主力净流入 | 主力净流入金额 |
| 526792 | 振幅 | 振幅百分比 |

前端通过 `data["价格"]`、`data["涨幅"]` 等中文 key 访问字段值。

### 4.5 API 客户端配置

**文件**: `web/js/api.js`

前端通过 `window.__THS_API_BASE__` 全局变量配置后端地址：

```javascript
const API_BASE = window.__THS_API_BASE__ || "";
```

- **默认值** `""`：API 请求发往前端同域（适用于同源部署或开发代理）
- **设置方式**：在 `index.html` 的 `<script>` 标签中、`router.js` 加载前设置

```html
<!-- 本地开发：前端 port 3000，后端 port 8000 -->
<script>window.__THS_API_BASE__ = "http://localhost:8000";</script>
```

**api 对象方法速查**：

```javascript
import { api } from "./api.js";

// 市场行情
api.marketCN("USZA300033", "基础数据")
api.marketUS("UNQQTSLA")
api.marketHK("UHKM00700")
api.marketIndex("USHI000001,USZI399001")
api.marketBlock("URFI883404")

// 个股
api.klines("USZA300033", 100, "day", "")
api.intraday("USZA300033")
api.depth("USZA300033")
api.bigOrderFlow("USZA300033")
api.callAuction("USZA300033")

// 列表
api.industry()
api.concept()
api.stockCN()
api.stockUS()
api.stockHK()
api.indexList()
api.blockConstituents("URFI883404")

// 杂项
api.search("同花顺")
api.completeCode("300033")
api.news("1A0001", "USHI")
api.ipoToday()
api.health()
```

### 4.6 工具函数

**文件**: `web/js/utils.js`

| 函数 | 签名 | 说明 |
|------|------|------|
| `formatPrice` | `(val) => string` | 格式化价格，保留 2 位小数，null 返回 `"--"` |
| `formatChange` | `(val) => string` | 格式化涨跌额，正数前加 `+`，如 `"+0.53"` |
| `formatChangePct` | `(val) => string` | 格式化涨跌幅，正数前加 `+`，如 `"+0.53%"` |
| `formatVolume` | `(vol) => string` | 格式化成交量，>=1亿显示"亿"，>=1万显示"万" |
| `formatAmount` | `(amt) => string` | 格式化金额，>=1亿显示"亿"，>=1万显示"万" |
| `colorClass` | `(val) => string` | 返回 `"up"`（正数/红）、`"down"`（负数/绿）或 `""`（零） |
| `formatTime` | `(timeStr) => string` | 格式化时间，ISO 字符串转为 `HH:MM` |
| `formatDate` | `(timeStr) => string` | 格式化日期，ISO 字符串转为本地日期 |
| `debounce` | `(fn, ms) => function` | 防抖函数，返回包装后的函数 |
| `el` | `(tag, attrs, children) => HTMLElement` | 快速创建 DOM 元素 |
| `clear` | `(el) => void` | 清空 DOM 元素的所有子节点 |

**CSS 颜色类**（在 `css/style.css` 中定义）：

| 类名 | 颜色 | 用途 |
|------|------|------|
| `.up` | `#f85149`（红色）| 上涨/正数 |
| `.down` | `#3fb950`（绿色）| 下跌/负数 |
| `.up-bg` | 红色半透明背景 | 上涨行背景 |
| `.down-bg` | 绿色半透明背景 | 下跌行背景 |

---

## 5. 本地开发

### 前置条件

- Python 3.9+（已安装 thsdk）
- Node.js 不需要（前端无构建步骤）

### 启动后端

```bash
# 在项目根目录
cd server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

验证后端启动：

```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

### 启动前端

```bash
# 在项目根目录
cd web
python -m http.server 3000
```

### 配置跨域

前端（localhost:3000）和后端（localhost:8000）端口不同，需要配置：

**方法一**：在 `web/index.html` 的 `<head>` 中、`router.js` 引入前添加：

```html
<script>window.__THS_API_BASE__ = "http://localhost:8000";</script>
```

**方法二**：使用后端代理（不修改前端代码）：

```bash
# 后端默认 CORS_ORIGINS="*" 允许所有来源
# 如需限制，设置环境变量：
CORS_ORIGINS=http://localhost:3000 uvicorn main:app --port 8000
```

### 验证功能

打开浏览器 `http://localhost:3000`，依次测试：

1. **市场总览**：首页应显示 5 个指数卡片和涨跌榜
2. **搜索**：导航栏输入"同花顺"按回车，或点击"搜索"页
3. **个股详情**：点击搜索结果或涨跌榜中的股票，应显示 K 线图和盘口
4. **板块**：点击"板块"，切换行业/概念 Tab，点击板块查看成分股
5. **K 线切换**：在详情页点击不同周期按钮（分时/1分/日K 等）

---

## 6. 部署指南

### 6.1 后端部署

后端需要运行在支持 thsdk 原生 C 库的环境中。

#### Railway

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录并初始化
railway login
railway init

# 部署
railway up
```

`railway.toml` 或 `railway.json` 示例：

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd server && uvicorn main:app --host 0.0.0.0 --port $PORT"
  }
}
```

#### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r server/requirements.txt

WORKDIR /app/server
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 环境变量

生产环境应设置：

```bash
# 账户信息
THS_USERNAME=your_username
THS_PASSWORD=your_password
THS_MAC=your_mac_address

# CORS（设为前端域名）
CORS_ORIGINS=https://your-app.vercel.app

# 可选
API_PORT=8000
```

### 6.2 前端部署 (Vercel)

**文件**: `web/vercel.json`

```json
{
  "buildCommand": null,
  "outputDirectory": ".",
  "cleanUrls": true,
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

#### 部署步骤

1. 在 Vercel Dashboard 中创建新项目
2. Root Directory 设置为 `web`
3. Framework Preset 选择 `Other`
4. Build Command 留空
5. Output Directory 设为 `.`
6. Deploy

#### 配置后端地址

部署后，需要在前端配置后端 API 地址。修改 `web/index.html`：

```html
<script>window.__THS_API_BASE__ = "https://your-backend.railway.app";</script>
```

或者使用 Vercel 环境变量 + rewrite 代理（更安全，避免暴露后端地址）：

修改 `web/vercel.json`：

```json
{
  "buildCommand": null,
  "outputDirectory": ".",
  "cleanUrls": true,
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-backend.railway.app/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

这样前端的 API 请求会自动代理到后端，无需设置 `__THS_API_BASE__`。

### 6.3 跨域配置

| 部署方式 | 后端 CORS | 前端 API_BASE | 说明 |
|----------|-----------|---------------|------|
| 本地开发 | `CORS_ORIGINS=*` | `http://localhost:8000` | 开发环境宽松配置 |
| Vercel + Railway | `CORS_ORIGINS=https://xxx.vercel.app` | `https://xxx.railway.app` | 生产环境限制来源 |
| Vercel rewrite 代理 | 不需要 CORS | `""` (同域) | Vercel 层面代理，无跨域问题 |

---

## 7. 二次开发指南

### 7.1 新增后端 API 端点

1. 在 `server/routes/` 对应文件中添加新的路由函数：

```python
# server/routes/stock.py
@router.get("/new-endpoint")
async def new_endpoint(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.some_sdk_method(ths_code)       # 调用 thsdk 方法
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
```

2. 所有路由通过闭包 `_query(ths)` 的形式传给 `connection.execute()`，确保线程安全
3. 路由自动注册（`main.py` 已 include 了所有路由模块）

### 7.2 新增前端页面

1. 创建 `web/pages/newpage.js`，导出 `renderNewPage` 函数：

```javascript
// web/pages/newpage.js
import { api } from "../js/api.js";

export function renderNewPage() {
    const app = document.getElementById("app");
    app.innerHTML = `<div class="section-title">新页面</div>`;

    // 加载数据、渲染 DOM
}
```

2. 在 `web/js/router.js` 中注册路由：

```javascript
import { renderNewPage } from "../pages/newpage.js";

const routes = [
    // ...existing routes
    { pattern: /^\/newpage$/, handler: renderNewPage },
];
```

3. 在 `web/index.html` 导航栏中添加链接：`<a href="#/newpage">新页面</a>`

### 7.3 新增市场支持

后端 `market.py` 中 `MARKET_METHODS` 字典控制了支持的市场：

```python
MARKET_METHODS = {
    "cn": "market_data_cn",
    "us": "market_data_us",
    # 添加新市场：
    "bond": "market_data_bond",
    "fund": "market_data_fund",
}
```

添加后即可通过 `/api/market/bond?codes=...` 访问。

---

## 附录：完整文件职责速查

| 文件 | 行数 | 职责 |
|------|------|------|
| `server/main.py` | ~35 | FastAPI 入口、CORS、路由注册、生命周期管理 |
| `server/config.py` | ~6 | 环境变量读取 |
| `server/connection.py` | ~108 | THSSingletonConnection 单例、自动重连、线程安全 |
| `server/schemas.py` | ~25 | Pydantic 查询参数模型 |
| `server/routes/market.py` | ~43 | 7 个市场行情端点 |
| `server/routes/stock.py` | ~104 | 5 个个股数据端点 |
| `server/routes/catalog.py` | ~55 | 7 个板块/列表端点 + 成分股端点 |
| `server/routes/misc.py` | ~81 | 4 个搜索/杂项端点 |
| `web/index.html` | ~20 | SPA 入口 HTML |
| `web/css/style.css` | ~340 | 暗色主题全局样式 |
| `web/js/api.js` | ~48 | REST API 客户端封装 |
| `web/js/utils.js` | ~95 | 格式化、DOM 工具函数、常量 |
| `web/js/router.js` | ~38 | Hash 路由与导航搜索 |
| `web/pages/overview.js` | ~126 | 市场总览页 |
| `web/pages/detail.js` | ~280 | 个股详情页（K线图） |
| `web/pages/search.js` | ~60 | 搜索页 |
| `web/pages/sectors.js` | ~140 | 板块页 |
| `web/vercel.json` | ~6 | Vercel 部署配置 |
