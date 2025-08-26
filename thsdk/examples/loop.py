from thsdk import THS
import time

with THS() as ths:
    for i in range(100):
        start_time = time.perf_counter()
        response = ths.stock_bj_lists()
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"第{i}次,耗时: {execution_time:.3f} 秒 {response}")

    time.sleep(1)
