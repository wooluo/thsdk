from thsdk import THS
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps

bj_tz = ZoneInfo('Asia/Shanghai')


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"函数 {func.__name__} 运行时间: {execution_time:.5f} 秒")
        return result

    return wrapper


with THS() as ths:
    # 查询历史近100条日k数据
    start_time = time.perf_counter()
    response = ths.klines("USZA300033", count=100)
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("查询历史近100条日k数据:")
    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))
    print(f"运行时间: {execution_time:.5f} 秒\n")
    time.sleep(1)

    # 查询历史20240101 - 202050101 日k数据
    start_time = time.perf_counter()
    response = ths.klines("USZA300033",
                          start_time=datetime(2024, 1, 1).replace(tzinfo=bj_tz),
                          end_time=datetime(2025, 1, 1).replace(tzinfo=bj_tz))
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("查询历史20240101 - 20250101 日k数据:")
    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))
    print(f"运行时间: {execution_time:.5f} 秒\n")
    time.sleep(1)

    # 查询历史100条日k数据 前复权
    start_time = time.perf_counter()
    response = ths.klines("USZA300033", count=100, adjust="forward")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("查询历史100条日k数据 前复权:")
    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))

    print(f"运行时间: {execution_time:.5f} 秒\n")
    time.sleep(1)

    # 查询历史100个1分钟k数据
    start_time = time.perf_counter()
    response = ths.klines("USZA300033", count=100, interval="1m")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("查询历史100个1分钟k数据:")
    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))
    print(f"运行时间: {execution_time:.5f} 秒\n")
    time.sleep(1)
