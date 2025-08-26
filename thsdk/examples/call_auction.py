from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    start_time = time.perf_counter()
    response = ths.call_auction("USZA300033")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("集合竞价:")
    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))
    print(f"运行时间: {execution_time:.5f} 秒\n")

    df = pd.DataFrame(response.get_result())
    df['匹配量'] = df['当前量']
    df['未匹配量'] = df['买2量'] - df['卖2量']
    df['时间'] = pd.to_datetime(df['时间'], unit='s').dt.tz_localize("UTC").dt.tz_convert("Asia/Shanghai")

    df = df.drop('当前量', axis=1)
    df = df.drop('买2量', axis=1)
    df = df.drop('卖2量', axis=1)

    print("合并数据后:")
    print(df)



    time.sleep(1)
