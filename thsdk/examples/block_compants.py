from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.block_components("URFI886037")
    print("板块成份股数据:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)
