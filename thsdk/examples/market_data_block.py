import time
from thsdk import THS
import pandas as pd


def main():
    """
    block_id:   0x4 沪封闭式基金
                        0x5 深封闭式基金
                        0x6 沪深封闭式基金
                        0xE 沪深A股
                        0x15 沪市A股
                        0x1B 深市A股
                        0xD2 全部指数
                        0xC5E3 北京A股
                        0xCFE4 创业板
                        0xCBE5 科创板
                        0xDBC6 风险警示
                        0xDBC7 退市整理
                        0xF026 行业和概念
                        0xCE5E 概念
                        0xCE5F 行业
                        0xdffb 地域
                        0xD385 国内外重要指数
                        0xDB5E 股指期货
                        0xCE3F 上证系列指数
                        0xCE3E 深证系列指数
                        0xCE3D 中证系列指数
                        0xC2B0 北证系列指数
                        0xCFF3 ETF基金
                        0xC6A6 全部A股
                        0xEF8C LOF基金
                        0xD811 分级基金
                        0xD90C T+0基金
                        0xC7B1 沪REITs
                        0xC7A0 深REITs
                        0xC89C 沪深REITs
                        0xCE14 可转债
                        0xCE17 国债
                        0xCE0B 上证债券
                        0xCE0A 深证债券
                        0xCE12 回购
                        0xCE11 贴债
                        0xCE16 地方债
                        0xCE15 企业债
                        0xD8D4 小公募
    :return:
    """
    ths = THS()
    block_code = 0xCE5F
    try:
        # 连接到行情服务器
        response = ths.connect()
        if not response.is_success():
            print(f"登录错误:{response.err_info}")
            return

        response = ths.block_data(block_code)
        df = pd.DataFrame(response.get_result())
        # print(df)

        urfi_codes = df['代码'].tolist()

        response = ths.market_data_block(urfi_codes)
        df = pd.DataFrame(response.get_result())
        # pd.set_option('display.max_columns', None)
        print(df)

        response = ths.market_data_block(urfi_codes, "扩展")
        df = pd.DataFrame(response.get_result())
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
