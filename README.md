# THSDK

[![PyPI version](https://badge.fury.io/py/thsdk.svg)](https://badge.fury.io/py/thsdk)

**thsdk** available on PyPi:

## Installation

```bash
pip install --upgrade thsdk
```

## Usage

```python
from thsdk import THS
import pandas as pd

with THS() as ths:
    response = ths.klines("USZA300033", count=100)
    print(pd.DataFrame(response.get_result()))


```

```
            时间     收盘价       成交量         总金额     开盘价     最高价     最低价
0   2025-01-06  252.85  10878507  2768722600  255.01  260.78  251.00
1   2025-01-07  261.00  14048646  3622089800  254.30  261.68  252.47
2   2025-01-08  258.91  14114265  3629279900  257.15  264.90  251.00
3   2025-01-09  257.88   8247352  2138059000  256.86  262.88  256.50
4   2025-01-10  250.55   9171541  2341876100  258.57  260.38  250.20
..         ...     ...       ...         ...     ...     ...     ...
96  2025-06-04  249.70   5294327  1318386680  246.00  251.38  244.80
97  2025-06-05  254.11   6488422  1636593300  249.73  255.55  248.46
98  2025-06-06  249.50   4678326  1173537940  254.18  254.80  249.00
99  2025-06-09  255.24   7754966  1976886800  249.72  257.00  249.72
100 2025-06-10  248.88   6180978  1548168800  255.00  255.77  246.50

[101 rows x 7 columns]
```

更多案例在thsdk库目录下的[thsdk/examples]()。

## Links

- [同花顺量化平台](https://quant.10jqka.com.cn/view/)
- [同花顺数据接口](https://quantapi.10jqka.com.cn/)
- [同花顺智能交易](https://www.forfunds.cn/platform/pcweb/productCenter/expert/)
- [同花顺PythonTrader智能交易](https://xdres.10jqka.com.cn/help/python/site/)
- [同花顺python策略器API](https://www.showdoc.com.cn/THSPythonSE/3269126718101134)
- [同花顺高频行情接口 L1，L2](https://www.forfunds.cn/platform/pcweb/productCenter/DataFeed/)

- 开通同花顺python策略编辑器和网格权限QQ群：1164717242，832421882