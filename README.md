# THSDK

THSDK 是一个用于股市金融行情数据的 Python SDK，提供便捷的 API 接口来获取股票、期货、外汇等金融市场数据。该库封装了同花顺底层 C 动态链接库，支持实时数据查询、历史 K 线、分时数据、板块数据等功能。

## 安装

```bash
pip install --upgrade thsdk
```

### 系统要求

- Python 3.9+
- 支持的操作系统：Linux (x86_64, arm64), macOS (Intel, Apple Silicon), Windows

## 快速开始

```python
from thsdk import THS

with THS() as ths:
    # 搜索股票
    result = ths.search_symbols("同花顺")
    print(result.data)

    # 获取 K 线
    klines = ths.klines("USZA300033", count=100)
    if klines.success:
        print(klines.df.head())
```

## 市场代码格式

所有证券代码使用 THS 格式：`4位市场前缀 + 证券代码`。

| 市场 | 前缀 | 示例 |
|------|------|------|
| 沪市 A 股 | `USHA` | `USHA600519`（贵州茅台） |
| 深市 A 股 | `USZA` | `USZA300033`（同花顺） |
| 北交所 | `USTM` | `USTM430047` |
| 美股 | `UNQQ` / `UNQS` | `UNQQTSLA`（特斯拉） |
| 港股 | `UHKM` / `UHKG` | `UHKM00700`（腾讯） |
| 上证指数 | `USHI` | `USHI000001` |
| 深证指数 | `USZI` | `USZI399001` |
| 行业/概念板块 | `URFI` | `URFI883404` |
| 期货 | `UGFF` | `UGFFIF00` |
| 外汇 | `UFXB` | `UFXBUSDCNY` |

如果不知道完整代码，可以用以下方式获取：

```python
ths.search_symbols("贵州茅台")   # 按名称搜索
ths.complete_ths_code("600519")  # 按代码补全
```

## API 参考

### 连接管理

```python
ths = THS()
resp = ths.connect()   # 连接服务器
# ... 查询数据 ...
ths.disconnect()       # 断开连接

# 或使用上下文管理器自动管理
with THS() as ths:
    pass
```

### 账户配置

优先级从高到低：

1. **直接传入参数**：`THS({"username": "...", "password": "...", "mac": "..."})`
2. **环境变量**：`THS_USERNAME`、`THS_PASSWORD`、`THS_MAC`
3. **临时游客账户**：`THS()` 无参数（仅测试用，有权限限制）

### 实时行情

```python
# A股行情 - query_key: "基础数据", "基础数据2", "基础数据3", "扩展1", "扩展2", "汇总"
resp = ths.market_data_cn("USHA600519", query_key="汇总")
# 返回字段: 价格, 涨跌, 涨幅, 名称, 代码, 成交量, 总金额, 昨收价, 开盘价, 最高价, 最低价, 换手率

# 批量查询
resp = ths.market_data_cn(["USHA600519", "USZA300033"], query_key="基础数据")

# 美股 - query_key: "基础数据", "每股净资产", "每股收益", "净利润", "财务指标"
resp = ths.market_data_us("UNQQTSLA", query_key="基础数据")

# 港股 - query_key: "基础数据", "每股净资产", "净利润", "财务指标"
resp = ths.market_data_hk("UHKM00700", query_key="基础数据")

# 指数 - query_key: "基础数据", "扩展"
resp = ths.market_data_index("USHI000001", query_key="基础数据")

# 其他市场
resp = ths.market_data_block("URFI883404", query_key="基础数据")   # 板块
resp = ths.market_data_future("UGFFIF00", query_key="基础数据")    # 期货
resp = ths.market_data_forex("UFXBUSDCNY", query_key="基础数据")   # 外汇
```

### K 线数据

```python
# interval: "1m", "5m", "15m", "30m", "60m", "120m", "day", "week", "month", "quarter", "year"
# adjust: ""（不复权）, "前复权", "后复权"
resp = ths.klines("USZA300033", count=100, interval="day", adjust="前复权")
# 返回字段: 时间, 开盘价, 最高价, 最低价, 收盘价/价格, 成交量, 总金额
```

**返回示例：**
```json
{
  "success": true,
  "data": [
    {"时间": "2026-03-11 00:00:00", "收盘价": 324.64, "开盘价": 321.1, "最高价": 326.5, "最低价": 318.44, "成交量": 8073410}
  ]
}
```

### 分时数据

```python
resp = ths.intraday_data("USZA300033")          # 当日分时
resp = ths.min_snapshot("USZA300033", date="20240315")  # 历史分时
```

### 盘口深度

```python
resp = ths.depth("USZA300033")          # 5档盘口
resp = ths.order_book_ask("USZA300033") # 卖方深度
resp = ths.order_book_bid("USZA300033") # 买方深度
# 返回字段: 买1价...买5价, 买1量...买5量, 卖1价...卖5价, 卖1量...卖5量, 昨收价
```

### 大单资金流

```python
resp = ths.big_order_flow("USHA600519")
# 返回字段: 大单流入, 大单流出, 主力净量
```

### 集合竞价

```python
resp = ths.call_auction("USZA300033")          # 集合竞价
resp = ths.call_auction_anomaly("USHA")        # 竞价异动
```

### Tick 数据

```python
resp = ths.tick_level1("USZA300033")            # 3秒 tick
resp = ths.tick_super_level1("USZA300033")      # 超级盘口（含委托档位）
```

### 板块与列表

```python
# 板块数据
resp = ths.ths_industry()                       # 行业板块列表
resp = ths.ths_concept()                        # 概念板块列表
resp = ths.block_constituents("URFI883404")     # 板块成分股

# 市场列表
resp = ths.stock_cn_lists()    # A股列表
resp = ths.stock_us_lists()    # 美股列表
resp = ths.stock_hk_lists()    # 港股列表
resp = ths.index_list()        # 指数列表
resp = ths.forex_list()        # 外汇列表
resp = ths.futures_lists()     # 期货列表
resp = ths.bond_lists()        # 债券列表
resp = ths.fund_etf_lists()    # ETF基金列表
```

### 搜索与补全

```python
resp = ths.search_symbols("同花顺")              # 模糊搜索
resp = ths.search_symbols("同花顺", "SH,SZ")    # 按市场过滤
resp = ths.search_symbols("300033")             # 按代码搜索
resp = ths.complete_ths_code("300033")          # 代码补全
resp = ths.complete_ths_code(["300033", "TSLA"])# 批量补全
```

**返回示例：**
```json
{
  "success": true,
  "data": [
    {"THSCODE": "USZA300033", "Name": "同花顺", "Code": "300033", "MarketStr": "USZA", "MarketDisplay": "深A"}
  ]
}
```

### 新闻与 IPO

```python
resp = ths.news(code="1A0001", market="USHI")   # 资讯
resp = ths.ipo_today()                           # 今日上市新股
resp = ths.ipo_wait()                            # 待上市新股
```

### 问财查询

```python
resp = ths.wencai_nlp("涨停")   # 自然语言选股
```

### 其他接口

```python
resp = ths.corporate_action("USZA300033")  # 权息资料（分红送转）
resp = ths.market_block("UFXB")            # 按市场查板块
resp = ths.help("doc")                     # 帮助信息
```

## Response 对象

所有 API 返回 `Response` 对象：

```python
response.success  # bool - 是否成功
response.error    # str  - 错误信息
response.data     # list[dict] / dict / str - 数据
response.extra    # dict - 额外信息（如 ServerDelay）
response.df       # pd.DataFrame - 自动转为 DataFrame
response.to_dict()  # 序列化为 dict
```

字段名均为中文（如 "价格"、"涨幅"、"成交量"）。

## 示例代码

项目包含丰富的示例，位于 `src/thsdk/examples/` 目录：

```bash
# 运行单个示例
python -m thsdk.examples.kline

# 语法检查全部示例
python -m thsdk.examples.run_all_examples

# 顺序执行全部示例
python -m thsdk.examples.run_all_examples --mode live
```

### Web 查询工具

```bash
python -m thsdk.examples.webapp --host 127.0.0.1 --port 8765
```

## OpenClaw Skill

本仓库包含一个 [OpenClaw](https://openclaw.ai) 技能文件 `skills/thsdk/SKILL.md`，可让 AI 智能体直接调用 thsdk 获取股票数据。将 `skills/thsdk/` 目录复制到 `~/.agents/skills/` 或 `~/.openclaw/skills/` 即可启用。

## 目录结构

```
src/thsdk/
  thsdk.py          # 对外聚合入口
  base.py           # 连接、动态库调用
  domestic.py       # 国内固定长度行情接口
  catalog.py        # 板块与市场列表接口
  market_queries.py # market_data_* 系列通用查询
  misc_api.py       # 搜索、问财、资讯、IPO
  response.py       # Response / Payload
  query_configs.py  # 查询配置常量
  validators.py     # 市场与代码规则
  examples/         # 示例代码
skills/thsdk/
  SKILL.md          # OpenClaw 技能定义
```

## 许可证

MIT License。详见 [LICENSE](LICENSE) 文件。
