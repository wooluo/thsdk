from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.normalize_symbol("300033")
    print("补齐单个:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    codes = ["300033", "600519", "TSLA", "APPL", "159316", "1A0001"]
    response = ths.normalize_symbol(codes)
    print("补齐多个:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    if len(codes) < len(response.get_result()):
        print("可能获取到多市场数据，检查代码")
    if len(codes) > len(response.get_result()):
        print("补齐错误于原数据数量不匹配")
    time.sleep(1)
