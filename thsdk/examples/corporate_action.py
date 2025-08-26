from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    start_time = time.perf_counter()
    response = ths.corporate_action("USZA300033")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("权息资料:")

    if not response.is_success():
        print(response.err_info)
    else:
        print(pd.DataFrame(response.get_result()))
    print(f"运行时间: {execution_time:.5f} 秒\n")

    time.sleep(1)
