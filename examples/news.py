from thsdk import THS
import pandas as pd
import time


def main():
    ths = THS()
    try:

        response = ths.connect()
        if not response:
            print(f"❌ 连接失败: {response.error}")
            return

        response = ths.news()
        if response.success:
            df = response.df
            print("\n=== 7X24快讯最新新闻 ===")
            if df.empty:
                print("没有数据")
            else:
                print(df)

        response = ths.news(text_id=0x2001)
        if response.success:
            df = response.df
            print("\n=== 7X24快讯重要新闻 ===")
            if df.empty:
                print("没有数据")
            else:
                print(df)

        response = ths.news(text_id=0x3808, code="300033", market="USZA")
        if response.success:
            df = response.df
            print("\n=== 个股社区 ===")
            if df.empty:
                print("没有数据")
            else:
                print(df)

        response = ths.news(text_id=0x3805, code="300033", market="USZA")
        if response.success:
            df = response.df
            print("\n=== 个股公告 ===")
            if df.empty:
                print("没有数据")
            else:
                print(df)

        response = ths.news(text_id=0x3806, code="300033", market="USZA")
        if response.success:
            df = response.df
            print("\n=== 个股研报 ===")
            if df.empty:
                print("没有数据")
            else:
                print(df)

        print("✅ 成功连接到行情服务器\n")

        time.sleep(0.5)


    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

    finally:
        # 断开连接
        ths.disconnect()
        print("✅ 已成功断开与服务器的连接\n")


if __name__ == "__main__":
    main()

