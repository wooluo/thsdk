from thsdk import THS
import pandas as pd
import time


def main():
    ths = THS()
    try:
        # 连接到行情服务器
        response = ths.connect()
        if not response.is_success():
            print(f"登录错误:{response.err_info}")
            return

        # 获取纳斯达克股票列表
        response = ths.bond_lists()
        df = pd.DataFrame(response.get_result())

        # 按代码前四位分组
        df['code_prefix'] = df['代码'].str[:4]
        grouped_codes = df.groupby('code_prefix')['代码'].apply(list).to_dict()

        # 存储所有分组的数据
        all_data = []

        # 按分组获取股票市场数据
        for prefix, codes in grouped_codes.items():
            print(f"正在处理前缀: {prefix}")
            response = ths.market_data_bond(codes)
            time.sleep(0.1)
            if not response.is_success():
                print(f"前缀 {prefix} 错误信息: {response.err_info}")
                continue

            # 将获取的数据添加到总列表
            if response.get_result():
                all_data.extend(response.get_result())

        # 将所有数据转换为DataFrame
        if all_data:
            result_df = pd.DataFrame(all_data)
            print("股票市场数据:")
            # pd.set_option('display.max_columns', None)
            print(result_df)
            print("查询成功 数量:", len(result_df))
        else:
            print("未获取到任何数据")

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # 断开连接
        ths.disconnect()
        print("Disconnected from the server.")

    time.sleep(1)


if __name__ == "__main__":
    main()
