import time
from thsdk import THS
import pandas as pd


def main():
    ths = THS()
    ths_code = "USZA300033"
    try:
        # 连接到行情服务器
        response = ths.connect()
        if not response.is_success():
            print(f"登录错误:{response.err_info}")
            return

        response = ths.order_book_ask(ths_code)
        df = pd.DataFrame(response.get_result())
        print("\n=== 市场深度卖方 ===")
        if df.empty:
            print("没有数据")
        else:
            print(df)

        response = ths.order_book_bid(ths_code)
        df = pd.DataFrame(response.get_result())
        print("\n=== 市场深度买方 ===")
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
