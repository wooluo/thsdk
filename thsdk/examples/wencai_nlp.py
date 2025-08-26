import time
from thsdk import THS
import pandas as pd


# with THS() as ths:
#     response = ths.wencai_nlp("龙头行业;国资委;所属行业")
#     df = pd.DataFrame(response.get_result())
#     print(df)
#
#     time.sleep(1)
#

def main():
    ths = THS()
    try:
        # 连接到行情服务器
        response = ths.connect()
        if not response.is_success():
            print(f"登录错误:{response.err_info}")
            return

        response = ths.wencai_nlp("龙头行业;国资委;所属行业")
        df = pd.DataFrame(response.get_result())

        def complete_code(code):
            if code.endswith(".SH"):
                return f"USHA{code[:6]}"
            elif code.endswith(".SZ"):
                return f"USZA{code[:6]}"
            elif code.endswith(".BJ"):
                return f"USTM{code[:6]}"
            else:
                raise ValueError("Unsupported code format", code)

        df['转换股票代码'] = [complete_code(code) for code in df['股票代码'].astype(str).tolist()]
        # pd.set_option('display.max_columns', None)
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
