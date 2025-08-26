from thsdk import THS
import pandas as pd
import time
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    response = ths.stock_cn_lists()
    print("A股:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.stock_us_lists()
    print("美股:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.nasdaq_lists()
    print("纳斯达克:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.stock_hk_lists()
    print("港股:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.stock_b_lists()
    print("B股:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.stock_bj_lists()
    print("北交所:")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)
