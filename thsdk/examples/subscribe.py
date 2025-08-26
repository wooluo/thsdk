import threading
import time
from ctypes import c_char_p, CFUNCTYPE
from thsdk import THS, Response
import pandas as pd
import json

# 用于控制线程退出的全局事件
exit_event = threading.Event()


# 定义回调函数
@CFUNCTYPE(None, c_char_p)
def callback(data: c_char_p):
    try:
        decoded_data = data.decode('utf-8')
        print(f"TEST: {decoded_data}")
    except UnicodeDecodeError:
        print("回调数据解码失败")


@CFUNCTYPE(None, c_char_p)
def callback_tick(data: c_char_p):
    try:
        decoded_data = Response(data.decode('utf-8'))
        print(f"TICK: {decoded_data}")
    except UnicodeDecodeError:
        print("回调数据解码失败")


@CFUNCTYPE(None, c_char_p)
def callback_l2(data: c_char_p):
    try:
        decoded_data = Response(data.decode('utf-8'))
        print(f"L2: {decoded_data}")
    except UnicodeDecodeError:
        print("回调数据解码失败")


@CFUNCTYPE(None, c_char_p)
def callback_order_book(data: c_char_p):
    try:
        decoded_data = Response(data.decode('utf-8'))
        print(f"DEPTH: {decoded_data}")
    except UnicodeDecodeError:
        print("回调数据解码失败")


def run_subscription():
    ths = THS()

    # 连接服务器
    response = ths.connect()
    if not response.is_success():
        print(f"连接失败: {response.err_info}")
        return

    sub_id = ""
    sub_id_tick = ""
    sub_id_l2 = ""
    # test
    response = ths.subscribe_test(callback=callback)
    if not response.is_success():
        print(f"订阅失败: {response.err_info}")
    else:
        sub_id = response.get_result().get("subscribe_id")
        print(f"订阅成功，订阅ID: {sub_id}, 结果: {response.err_info}")

    # tick  snapshot (暂时不再公开)
    response2 = ths.subscribe_tick("USZA300033", callback=callback_tick)
    if response2.err_info != "":
        print(f"订阅失败: {response2.err_info}")
    else:
        print(response2)
        sub_id_tick = response2.payload.result.get("subscribe_id")
        print(f"订阅成功，订阅ID: {sub_id_tick}, 结果: {response2.err_info}")

    # l2成交推送 (已经不再公开做了屏蔽，欢迎在官网接口 https://quant.10jqka.com.cn)
    response3 = ths.subscribe_l2("USZA300033", callback=callback_l2)
    if response3.err_info != "":
        print(f"订阅失败: {response3.err_info}")
    else:
        sub_id_l2 = response3.payload.result.get("subscribe_id")
        print(f"订阅成功，订阅ID: {sub_id_l2}, 结果: {response3.err_info}")

    # 等待退出信号
    try:
        while not exit_event.is_set():
            time.sleep(1)  # 降低 CPU 使用率
    except KeyboardInterrupt:
        print("订阅线程收到中断信号")
    finally:
        # 清理资源

        if sub_id != "":
            print(f"取消订阅ID: {sub_id}")
            ths.unsubscribe(sub_id)
        if sub_id_tick != "":
            print(f"取消订阅ID: {sub_id_tick}")
            ths.unsubscribe(sub_id_tick)
        if sub_id_l2 != "":
            print(f"取消订阅ID: {sub_id_l2}")
            ths.unsubscribe(sub_id_l2)

        ths.disconnect()
        print("✅ 订阅线程已清理资源并退出")


# 启动订阅线程
if __name__ == "__main__":
    subscription_thread = threading.Thread(target=run_subscription)
    subscription_thread.start()

    # 主线程可以执行其他任务
    try:
        while True:
            print("主线程运行中...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("主线程收到中断信号，通知订阅线程退出")
        exit_event.set()  # 通知订阅线程退出
        subscription_thread.join()  # 等待订阅线程结束
        print("✅ 主线程退出")
