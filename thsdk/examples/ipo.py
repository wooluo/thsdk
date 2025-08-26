import time
from thsdk import THS
import pandas as pd


def main():
    ths = THS()
    try:
        # 连接到行情服务器
        response = ths.connect()
        if not response.is_success():
            print(f"登录错误:{response.err_info}")
            return

        # 获取今日IPO
        response = ths.ipo_today()
        df = pd.DataFrame(response.get_result())
        print("\n=== 今日IPO ===")
        if df.empty:
            print("没有数据")
        else:
            print(df)

        # 获取IPO等待列表
        response = ths.ipo_wait()
        df = pd.DataFrame(response.get_result())
        print("\n=== IPO等待列表 ===")
        if df.empty:
            print("没有数据")
        else:
            print(df)

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # 断开连接
        ths.disconnect()
        print("Disconnected from the server.")

    time.sleep(1)


if __name__ == "__main__":
    main()
