from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.ths_concept()
    print("概念:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)
