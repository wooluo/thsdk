from thsdk import THS
import pandas as pd
import time
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    response = ths.index_list()
    df = pd.DataFrame(response.get_result())
    hs300_code = df.loc[df['名称'] == '沪深300', '代码']
    print("沪深300指数:")
    print(hs300_code)
    time.sleep(0.1)

    # Request K-line data for each code in 'hs300_code'
    for code in hs300_code:
        klines_response = ths.klines(code, count=100)
        if klines_response.is_success():
            klines_df = pd.DataFrame(klines_response.get_result())
            print(f"K-line data for {code}:")
            print(klines_df)
        else:
            print(f"Failed to fetch K-line data for {code}: {klines_response.err_info}")
        time.sleep(0.1)

    response = ths.wencai_nlp("沪深300 成份股")
    df = pd.DataFrame(response.get_result())
    print(df)

    time.sleep(1)
