from thsdk import THS
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Define the list of symbols to process
markets = ["USHA", "USZA"]

# Initialize an empty list to store results
all_results = []

# Define Beijing timezone
beijing_tz = ZoneInfo("Asia/Shanghai")

with THS() as ths:
    for market in markets:
        try:
            start_time = time.perf_counter()
            response = ths.call_auction_anomaly(market)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            print(f"\n竞价异动 {market}:")
            if not response.is_success():
                print(f"错误信息: {response.err_info}")
            else:
                result_df = pd.DataFrame(response.get_result())
                if not result_df.empty:
                    # result_df['market'] = market
                    # Convert Unix timestamp in '时间' to datetime in Beijing time
                    if '时间' in result_df.columns:
                        result_df['时间'] = pd.to_datetime(result_df['时间'], unit='s', errors='coerce').dt.tz_localize('UTC').dt.tz_convert(beijing_tz)
                    all_results.append(result_df)
                else:
                    print(f"{market}: 无数据返回")
            print(f"运行时间: {execution_time:.5f} 秒")

            time.sleep(0.1)  # Pause between requests to avoid overwhelming the API

        except Exception as e:
            print(f"处理 {market} 时发生错误: {str(e)}")

# Combine and sort results
if all_results:
    # Specify the columns (keys) to remove
    columns_to_remove = ['价格', '总金额']

    # Remove specified columns from each DataFrame in all_results
    all_results = [df.drop(columns=columns_to_remove, errors='ignore') for df in all_results]

    combined_df = pd.concat(all_results, ignore_index=True)
    # Sort by '时间' if it exists
    if '时间' in combined_df.columns:
        combined_df = combined_df.sort_values(by='时间', ascending=True, na_position='last')
        # Format the '时间' column for display in Beijing time
        combined_df['时间'] = combined_df['时间'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    else:
        print("\n警告: 未找到'时间'列，无法按时间排序")
    print("\n合并后的结果（按北京时间排序）:")
    # pd.set_option('display.max_rows', None)  # 显示所有列
    # pd.set_option('display.max_columns', None)  # 显示所有列
    print(combined_df)
else:
    print("\n无数据可合并")

print("\n所有符号处理完成")