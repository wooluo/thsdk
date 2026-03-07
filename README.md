# THSDK

THSDK 是一个用于股市金融行情数据的 Python SDK，提供便捷的 API 接口来获取股票、期货、外汇等金融市场数据。该库封装了ths底层 C 动态链接库，支持实时数据查询、历史 K 线、分时数据、板块数据等功能。

## 功能特性

- **多市场支持**：支持A股、美股、港股、期货、外汇等市场数据
- **丰富数据类型**：K线数据、分时数据、深度数据、板块数据、成交数据等
- **灵活查询**：支持单只股票批量查询、历史数据查询
- **易用接口**：Pythonic API 设计，支持上下文管理器
- **数据转换**：自动转换为 Pandas DataFrame，便于数据分析

## 安装

```bash
pip install --upgrade thsdk
```

### 系统要求

- Python 3.9+
- 支持的操作系统：Linux (x86_64, arm64), macOS (Intel), Windows
- 依赖库：pandas, orjson (可选，用于更快的 JSON 解析)

## 快速开始

```python
from thsdk import THS

# 使用上下文管理器自动处理连接
with THS() as ths:
    # 获取 K 线数据
    response = ths.klines("USZA300033", count=100)
    if response.success:
        df = response.df  # 自动转换为 DataFrame
        print(df.head())

```

### 账户配置

SDK 支持多种账户配置方式，优先级从高到低：

1. **直接传入参数**：
```python
ths = THS({
    "username": "your_username",
    "password": "your_password",
    "mac": "3e:8c:40:3e:0a:14"
})
```

2. **环境变量**：
```bash
export THS_USERNAME=your_username
export THS_PASSWORD=your_password
export THS_MAC=your_mac_address
```
```python
ths = THS()  # 自动读取环境变量
```

3. **临时游客账户**（仅用于测试，不推荐生产使用）：
```python
ths = THS()  # 自动使用临时账户
```

## API 参考

### THS 类

主要的客户端类，用于连接服务器和查询数据。

#### 初始化
```python
THS(ops: Optional[Dict[str, Any]] = None)
```

#### 连接管理
- `connect(max_retries: int = 5) -> Response`：连接到服务器
- `disconnect() -> None`：断开连接

#### 数据查询方法

##### K线数据
- `klines(ths_code: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, adjust: str = "", interval: str = "day", count: int = -1) -> Response`
  - 获取历史K线数据
  - `interval` 支持：1m, 5m, 15m, 30m, 60m, 120m, day, week, month, quarter, year
  - `adjust` 支持：forward（前复权）, backward（后复权）, ""（不复权）

##### 分时数据
- `intraday_data(ths_code: str) -> Response`：日内分时数据
- `min_snapshot(ths_code: str, date: Optional[str] = None) -> Response`：历史分时数据

##### 成交数据
- `tick_level1(ths_code: str) -> Response`：3秒tick成交数据
- `tick_super_level1(ths_code: str, date: Optional[str] = None) -> Response`：超级盘口数据（含委托档位）

##### 深度数据
- `depth(ths_code: Union[str, list]) -> Response`：5档深度数据
- `order_book_ask(ths_code: str) -> Response`：卖方深度
- `order_book_bid(ths_code: str) -> Response`：买方深度

##### 板块数据
- `block(block_id: int) -> Response`：获取板块数据
- `block_constituents(link_code: str) -> Response`：板块成分股
- `ths_industry() -> Response`：行业板块
- `ths_concept() -> Response`：概念板块
- `index_list() -> Response`：指数列表

##### 市场数据
- `market_data_cn(ths_code: Any, query_key: str = "基础数据") -> Response`：A股市场数据
- `market_data_us(ths_code: Any, query_key: str = "基础数据") -> Response`：美股市场数据
- `market_data_hk(ths_code: Any, query_key: str = "基础数据") -> Response`：港股市场数据
- `market_data_block(block_code: Any, query_key: str = "基础数据") -> Response`：板块市场数据

##### 证券查询
- `query_securities(pattern: str, needmarket: str = "") -> Response`：模糊查询证券代码
  - 支持按名称、代码、拼音查询股票、指数、基金、行业概念等完整的股票代码和市场
  - `pattern`：查询关键词（名称、代码等）
  - `needmarket`：指定市场范围，支持 "SH"（沪市）、"SZ"（深市）、"SH,SZ"（沪深）、"HK"（港股）、"NQ"（纳斯达克）等

##### 其他数据
- `call_auction(ths_code: str) -> Response`：集合竞价数据
- `big_order_flow(ths_code: str) -> Response`：大单数据
- `corporate_action(ths_code: str) -> Response`：权息资料
- `wencai_nlp(condition: str) -> Response`：自然语言查询

##### 列表查询
- `stock_cn_lists() -> Response`：A股列表
- `stock_us_lists() -> Response`：美股列表
- `stock_hk_lists() -> Response`：港股列表
- `forex_list() -> Response`：外汇列表
- `futures_lists() -> Response`：期货列表
- `bond_lists() -> Response`：债券列表
- `fund_etf_lists() -> Response`：ETF基金列表

### Response 类

API 响应的封装类。

#### 属性
- `success: bool`：是否成功
- `error: str`：错误信息
- `data: Optional[Union[Dict[str, Any], List[Dict], str]]`：响应数据
- `extra: Dict[str, Any]`：额外信息

#### 方法
- `df -> pd.DataFrame`：转换为 Pandas DataFrame

## 示例

项目提供了丰富的示例代码，位于 `thsdk/examples/` 目录：

- `kline.py`：K线数据查询
- `intraday_data.py`：分时数据查询
- `tick_level1.py`：Tick 数据查询
- `market_data_cn.py`：A股市场数据
- `block.py`：板块数据查询
- `query_securities.py`：证券模糊查询（支持多市场检索）
- `wencai_nlp.py`：问财查询
- 更多示例请查看 examples/ 目录

运行示例：
```bash
python thsdk/examples/kline.py
```

## 错误处理

所有 API 方法返回 `Response` 对象，检查 `response.success` 来判断是否成功：

```python
response = ths.klines("USZA300033", count=100)
if response.success:
    data = response.data
else:
    print(f"错误: {response.error}")
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 常见问题

1. **连接失败**：检查账户信息是否正确，或使用临时游客账户测试
2. **数据为空**：确认证券代码格式正确（10位，以市场代码开头）
3. **性能问题**：对于大量数据查询，考虑调整 `buffer_size` 参数
4. **时区问题**：所有时间数据自动转换为亚洲/上海时区

## 版本历史

- v1.0.0：初始版本，支持基础行情数据查询

