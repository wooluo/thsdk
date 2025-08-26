from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.block_data(0xCE5E)
    print("板块数据:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0x15)
    print("沪市A股:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0x1B)
    print("深市A股:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0xCA8B)
    print("北交所:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0xCFE4)
    print("创业板:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0xCFE4)
    print("科创板:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0xCE5E)
    print("概念:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    response = ths.block_data(0xCE5F)
    print("行业:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)
