# encoding: utf-8
import os
import sys
import json
import time
import logging
import platform
import ctypes as c
from zoneinfo import ZoneInfo
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from ._constants import FieldNameMap, MARKETS, BLOCK_MARKETS, rand_account, CALL_AUCTION_ANOMALY_MAP, \
    market_to_market_id

__all__ = ['THS', 'Response']

if sys.version_info < (3, 9):
    raise RuntimeError("此程序需要 Python 3.9 或更高版本，当前版本为 {}.{}.{}".format(
        sys.version_info.major, sys.version_info.minor, sys.version_info.micro))

tz = ZoneInfo('Asia/Shanghai')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)
logger = logging.getLogger(__name__)


def _int2time(scr: int) -> datetime:
    """将整数时间戳转换为 datetime 对象。

    Args:
        scr (int): 整数时间戳，包含年、月、日、小时、分钟信息。

    Returns:
        datetime: 转换后的 datetime 对象，带亚洲/上海时区。

    Raises:
        ValueError: 如果时间戳无效。
    """
    try:
        year = 2000 + ((scr & 133169152) >> 20) % 100
        month = (scr & 983040) >> 16
        day = (scr & 63488) >> 11
        hour = (scr & 1984) >> 6
        minute = scr & 63
        return datetime(year, month, day, hour, minute, tzinfo=tz)
    except ValueError as e:
        raise ValueError(f"无效的时间整数: {scr}, 错误: {e}")


def _convert_data_keys_list(data: List[Dict]) -> List[Dict]:
    """转换数据字段名称为中文。

    Args:
        data (List[Dict]): 包含字段名称的字典列表。

    Returns:
        List[Dict]: 字段名称转换为中文后的字典列表。
    """
    converted_data = []
    for entry in data:
        converted_entry = {}
        for key, value in entry.items():
            key_int = int(key) if key.isdigit() else key
            converted_entry[FieldNameMap.get(key_int, key)] = value
        converted_data.append(converted_entry)
    return converted_data


def _convert_data_keys_dict(data: Dict) -> Dict:
    """转换数据字段名称为中文。

    Args:
        data (List[Dict]): 包含字段名称的字典列表。

    Returns:
        List[Dict]: 字段名称转换为中文后的字典列表。
    """
    converted_data = {}
    for key, value in data.items():
        key_int = int(key) if key.isdigit() else key
        converted_data[FieldNameMap.get(key_int, key)] = value
    return converted_data


class THSAPIError(Exception):
    """API 异常基类。"""
    pass


@dataclass
class Payload:
    """API 响应数据类，用于存储和处理返回的数据。

    Attributes:
        result (Optional[Union[Dict[str, Any], List[Any], str]]): API 响应的主要数据，可能是字典、列表、字符串或 None。
        dict_extra (Optional[Dict[str, Any]]): 额外的元数据字典，默认为空字典。
    """

    result: Optional[Union[Dict[str, Any], List[Any], str]] = None
    dict_extra: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __repr__(self) -> str:
        if isinstance(self.result, list):
            data_preview = self.result[:2] if len(self.result) > 2 else self.result
            result_str = f"{data_preview!r}... ({len(self.result)} items)"
        else:
            result_str = f"{self.result!r}"
        return f"Payload(result={result_str}, dict_extra={self.dict_extra!r})"


class Response:
    """API 响应类，用于解析和处理 API 返回的 JSON 数据。

    Attributes:
        err_info (str): 错误信息，若为空表示成功。
        payload (Payload): 响应数据对象。
    """
    err_info: str
    payload: Payload

    def __init__(self, json_str: str):
        """初始化响应对象。

        Args:
            json_str (str): JSON 格式的响应字符串。

        Notes:
            如果 JSON 字符串无效，将记录错误并初始化为空数据。
        """
        try:
            try:
                import orjson
                # Use orjson if available
                data_dict: Dict[str, Any] = orjson.loads(json_str.encode('utf-8'))
            except ImportError:
                import json
                # Fallback to standard json if orjson is not available
                data_dict: Dict[str, Any] = json.loads(json_str)
        except Exception as e:
            data_dict: Dict[str, Any] = {}
            print(f"无效的 JSON 字符串: {e}")

        self.err_info = data_dict.get("err_info", "")

        payload_data = data_dict.get("payload", {})
        if not isinstance(payload_data, dict):
            raise TypeError("payload must be a dictionary or None")

        result = payload_data.get("result")
        if result is not None and not isinstance(result, (dict, list, str)):
            raise TypeError("result must be a dictionary, list, string, or None")
        if isinstance(result, list):
            result = _convert_data_keys_list(result or [])

        dict_extra = payload_data.get("dict_extra", {})
        if dict_extra is not None and not isinstance(dict_extra, dict):
            raise TypeError("extra_data must be a dictionary or None")
        if isinstance(dict_extra, dict):
            dict_extra = _convert_data_keys_dict(dict_extra or {})

        self.payload = Payload(result, dict_extra)

    def __repr__(self) -> str:
        """返回对象的字符串表示。

        Returns:
            str: 包含错误信息和数据对象的字符串表示。
        """
        return f"Response(err_info={self.err_info!r}, payload={self.payload})"

    def is_success(self) -> bool:
        """检查响应是否成功。

        Returns:
            bool: 如果 err_info 为空，则返回 True，否则返回 False。
        """
        return not self.err_info

    def get_result(self) -> Optional[Union[Dict[str, Any], List[Any], str]]:
        """获取 payload 的 result 字段。

        Returns:
            Optional[Union[Dict[str, Any], List[Any], str]]: result 字段的值。
        """
        return self.payload.result


def error_response(err_info: str) -> Response:
    """创建错误响应对象。

    Args:
        err_info (str): 错误信息字符串。

    Returns:
        Response: 包含错误信息和空 payload 的响应对象。
    """
    return Response(json.dumps({
        "err_info": err_info,
        "payload": {}
    }))


class THS:
    """该类封装了与行情服务器的交互，支持获取 K 线、成交、板块等数据，以及实时数据订阅。
    """

    def __init__(self, ops: Optional[Dict[str, Any]] = None):
        """初始化 API 客户端。

        Args:
            ops (Dict[str, Any], optional): 配置信息，包含用户名、密码等。默认为 None，若未提供则使用随机账户。
        """
        ops = ops or {}
        account = rand_account()
        ops.setdefault("username", account[0])
        ops.setdefault("password", account[1])
        self.ops = ops
        self._login = False

        lib_path = ""
        system = platform.system()
        arch = platform.machine()
        base_dir = os.path.dirname(__file__)
        if system == 'Linux':
            lib_path = os.path.join(base_dir, "libs", "linux", "hq.so")
        elif system == 'Darwin':
            if arch == 'arm64':
                raise THSAPIError('Apple M系列芯片暂不支持')
            lib_path = os.path.join(base_dir, "libs", "darwin", 'hq.dylib')
        elif system == 'Windows':
            lib_path = os.path.join(base_dir, "libs", "windows", 'hq.dll')
        if lib_path == "":
            raise THSAPIError(f'不支持的操作系统: {system}')

        self._lib = None

        self._callbacks = []
        try:
            self._lib = c.CDLL(lib_path)
            self._lib.Call.argtypes = [
                c.c_char_p,  # input: C 字符串指针
                c.c_char_p,  # out: C 字符串指针
                c.c_int,  # outLen: C 整数
                c.c_void_p  # callback: 通用指针
            ]
            self._lib.Call.restype = c.c_int  # 返回类型为 C 整数
        except OSError as e:
            raise THSAPIError(f"加载动态链接库 {lib_path} 失败: {e}")

    def __enter__(self):
        """上下文管理器入口，自动连接服务器。

        Returns:
            THS: 客户端对象自身。
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动断开服务器连接。"""
        self.disconnect()

    def lib_call(self, method: str, params: Optional[Union[str, dict, list]] = "",
                 buffer_size: int = 1024 * 1024, callback: Optional[c.CFUNCTYPE] = None) -> tuple[int, str]:
        """调用 C 动态链接库的 Call 函数，处理所有行情服务操作。
                内部方法，统一调用 C 动态链接库的 Call 函数，处理所有行情服务操作。

                该方法封装了对 C 动态链接库的调用，负责构造输入 JSON，分配输出缓冲区，调用 Call 函数，
                并解析返回结果。支持的操作包括连接、断开连接、查询数据、订阅和取消订阅等。

                Args:
                    method: 操作类型，可选值：
                        - "connect": 连接行情服务器
                        - "disconnect": 断开行情服务器连接
                        - "help": 获取帮助信息
                    params: 请求字符串，具体内容取决于操作类型：
                        - connect: 账户信息配置字典[JSON]
                        - unsubscribe: 订阅ID[STR]
                        - disconnect: [None]
                    callback: 回调函数，仅对 subscribe 操作有效，用于接收实时推送数据。
                              签名必须为 c.CFUNCTYPE(None, c_char_p)，接收 UTF-8 编码的 JSON 字符串。
                    buffer_size: 输出缓冲区大小（字节），默认为 1MB，需足够大以容纳返回数据。

                Returns:

                    tuple[int, str]: 包含状态码和返回数据的元组。状态码为 0 表示成功，负值表示错误；返回数据为 JSON 格式字符串。其他负值表示错误，具体如下：
                        - 0: 成功
                        - -1: 输出缓冲区太小
                        - -2: 输入参数无效
                        - -3: 内部错误
                        - -4: 查询失败
                        - -5: 未连接到服务器
                        - -6: 请求超时

                Raises:
                    THSAPIError: 如果调用 Call 失败、输出缓冲区解码失败或 JSON 序列化/反序列化错误。
                """
        input_json = {
            "method": method,
            "params": params,
        }

        try:
            input_json_bytes = json.dumps(input_json).encode('utf-8')
        except (TypeError, ValueError) as e:
            raise THSAPIError(f"JSON 序列化失败: {e}")

        output_buffer = c.create_string_buffer(buffer_size)
        current_buffer_size = buffer_size

        if callback:
            self._callbacks.append(callback)

        try:
            status = self._lib.Call(input_json_bytes, output_buffer, c.c_int(current_buffer_size), callback)
            try:
                result = output_buffer.value.decode('utf-8') if output_buffer.value else ""
            except UnicodeDecodeError:
                raise THSAPIError("[thsdk] 输出缓冲区解码失败，可能包含非 UTF-8 数据")
            return status, result
        finally:
            del output_buffer
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def call(self, method: str, params: Optional[Union[str, dict, list]] = "",
             buffer_size: int = 1024 * 1024, callback: Optional[c.CFUNCTYPE] = None) -> Response:
        if not self._login:
            return error_response(f"未登录")

        result_code, result = self.lib_call(method=method, params=params, buffer_size=buffer_size, callback=callback)

        if result_code == 0:
            response = Response(result)
            if not response.is_success():
                logger.info(f"call错误信息: {response.err_info}")
            return response
        elif result_code == -1:
            current_size_mb = buffer_size / (1024 * 1024)
            return error_response(
                f"缓冲区大小不足,当前大小: {current_size_mb:.2f} MB,需要调整扩大 buffer_size 接收返回数据")
        elif result_code == -6:
            response = Response(result)
            if not response.is_success():
                logger.info(f"请求超时: {response.err_info}")
            return response
        else:
            return error_response(f"错误代码: {result_code}, 未找到方法: {method}, 参数:{params}")

    def connect(self, max_retries: int = 5) -> Response:
        """连接到行情服务器。

        Args:
            max_retries (int, optional): 最大重试次数，默认为 5。

        Returns:
            Response: 包含连接结果的响应对象。

        Raises:
            ValueError: 如果 max_retries 小于或等于 0。
        """
        if not isinstance(max_retries, int) or max_retries <= 0:
            max_retries = 5

        for attempt in range(max_retries):
            try:
                buffer_size = 1024 * 10
                result_code, result = self.lib_call(method="connect", params=self.ops, buffer_size=buffer_size)
                if result_code != 0:
                    logger.error(f"❌ 错误代码: {result_code}, 连接失败")
                    return error_response(f"错误代码: {result_code}, 连接失败")
                response = Response(result)

                if response.err_info == "":
                    self._login = True
                    logger.info("✅ 成功连接到服务器")
                    return response
                else:
                    logger.warning(f"❌ 第 {attempt + 1} 次连接尝试失败: {response.err_info}")
            except Exception as e:
                logger.error(f"❌ 连接报错: {e}")
            time.sleep(2 ** attempt)
        logger.error(f"❌ 尝试 {max_retries} 次后连接失败")
        return error_response(f"尝试 {max_retries} 次后连接失败")

    def disconnect(self):
        """断开与行情服务器的连接。

        Notes:
            如果未连接，则记录已断开信息。
        """
        if self._login:
            self._login = False
            self.lib_call("disconnect")
            logger.info("✅ 已成功断开与行情服务器的连接")
        else:
            logger.info("✅ 已经断开连接")

    def query_data(self, params: dict, buffer_size: int = 1024 * 1024 * 2, max_attempts=5) -> Response:
        """查询行情数据指令

        Args:
            params (dict): 查询请求参数。(必须按照顺序输入参数包含字段: id,codelist,market,datatype,service)
            buffer_size (int, optional): 输出缓冲区大小（字节），默认为 2MB。
            max_attempts (int, optional): 最大尝试次数，默认为 5。

        Returns:
            Response: 包含查询结果的响应对象。

        Notes:
            如果未登录，返回未授权响应。
            如果缓冲区不足，会自动扩大缓冲区并重试。
        """
        if not self._login:
            return error_response(f"未登录")

        attempt = 0
        while attempt < max_attempts:
            result_code, result = self.lib_call(method=f'query_data', params=params,
                                                buffer_size=buffer_size)

            if result_code == 0:
                response = Response(result)
                if not response.is_success():
                    logger.info(f"查询数据错误信息: {response.err_info}")
                return response
            elif result_code == -1:
                current_size_mb = buffer_size / (1024 * 1024)
                new_size_mb = (buffer_size * 2) / (1024 * 1024)
                logger.info(f"缓冲区大小不足。当前大小: {current_size_mb:.2f} MB, "
                            f"新的大小: {new_size_mb:.2f} MB")
                time.sleep(0.1)
                buffer_size *= 2
                attempt += 1
                if attempt == max_attempts:
                    return error_response(f"达到最大尝试次数，错误代码: {result_code}, "
                                          f"请求: {params}, 最终缓冲区大小: {buffer_size}")
            else:
                return error_response(f"错误代码: {result_code}, 未找到请求数据: {params}")

        return error_response(f"意外错误: 达到最大尝试次数，请求: {params}")

    def block_data(self, block_id: int) -> Response:
        """获取板块数据。

        Args:
            block_id (int): 板块 ID，如 0xE 表示沪深A股。
                        0x4 沪封闭式基金
                        0x5 深封闭式基金
                        0x6 沪深封闭式基金
                        0xE 沪深A股
                        0x15 沪市A股
                        0x1B 深市A股
                        0xD2 全部指数
                        0xCA8B 北京A股 北交所
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

        Returns:
            Response: 包含板块数据的响应对象。

        Raises:
            ValueError: 如果 block_id 未提供。
        """

        if not block_id:
            return error_response("必须提供板块 ID")

        params = {
            "block_id": block_id,
        }

        return self.call(method="block_data", params=params)

    def market_block(self, market: str) -> Response:
        """获取板块数据。

        Args:
            UFXB 基本汇率
            UFXC 交叉汇率
            UFXR 反向汇率
            UIFF 中金所
            UCFS 上期所
            UCFD 大商所
            UCFZ 郑商所


        Returns:
            Response: 包含板块数据的响应对象。

        Raises:
            ValueError: 如果 block_id 未提供。
        """

        if not market:
            return error_response("必须提供market")

        params = {
            "market": market,
        }

        return self.call(method="market_block", params=params)

    def subscribe_test(self, callback: c.CFUNCTYPE) -> Response:
        """订阅实测试时行情数据。

        Args:
            callback (c.CFUNCTYPE): 回调函数，用于处理订阅数据，需为 c.CFUNCTYPE(None, c_char_p) 类型。

        Returns:
            Response: 包含订阅结果的响应对象。
        """
        result_code, result = self.lib_call(method=f'subscribe.test', callback=callback)
        if result_code == 0:
            response = Response(result)
            if not response.is_success():
                logger.info(f"订阅错误信息: {response.err_info}")
            return response
        else:
            return error_response(f"错误代码: {result_code}, 测试订阅失败")

    def subscribe_tick(self, ths_code: str, callback: c.CFUNCTYPE) -> Response:
        """RESTRICTED: 订阅3秒tick snapshot推送 (订阅类被限制不再公开开放)

        Args:
            callback (c.CFUNCTYPE): 回调函数，用于处理订阅数据，需为 c.CFUNCTYPE(None, c_char_p) 类型。

        Returns:
            Response: 包含订阅结果的响应对象。
        """
        result_code, result = self.lib_call(method=f'subscribe.tick', params=ths_code, callback=callback)
        if result_code == 0:
            response = Response(result)
            if not response.is_success():
                logger.info(f"订阅错误信息: {response.err_info}")
            return response
        else:
            return error_response(f"错误代码: {result_code}, 测试订阅失败")

    def subscribe_l2(self, ths_code: str, callback: c.CFUNCTYPE) -> Response:
        """RESTRICTED: 订阅l2成交推送 (订阅类被限制不再公开开放)

        Args:
            callback (c.CFUNCTYPE): 回调函数，用于处理订阅数据，需为 c.CFUNCTYPE(None, c_char_p) 类型。

        Returns:
            Response: 包含订阅结果的响应对象。
        """
        result_code, result = self.lib_call(method=f'subscribe.l2', params=ths_code, callback=callback)
        if result_code == 0:
            response = Response(result)
            if not response.is_success():
                logger.info(f"订阅错误信息: {response.err_info}")
            return response
        else:
            return error_response(f"错误代码: {result_code}, 测试订阅失败")

    def unsubscribe(self, subscribe_id: str) -> Response:
        """取消订阅实时行情数据。

        Args:
            subscribe_id (str): 订阅 ID，由 subscribe 方法返回。

        Returns:
            Response: 包含取消订阅结果的响应对象。
        """
        result_code, result = self.lib_call("unsubscribe", subscribe_id)
        if result_code == 0:
            response = Response(result)
            if not response.is_success():
                logger.info(f"订阅错误信息: {response.err_info}")
            return response
        else:
            return error_response(f"错误代码: {result_code}, 退订失败: {subscribe_id}")

    def block_components(self, link_code: str) -> Response:
        """获取板块成分股数据。

        Args:
            link_code (str): 板块代码，如 'URFI881273'。

        Returns:
            Response: 包含成分股数据的响应对象。

        Raises:
            ValueError: 如果 link_code 未提供。
        """

        if not link_code:
            return error_response("必须提供板块代码")

        params = {
            "link_code": link_code,
        }

        return self.call(method="block_components", params=params)

    def tick_level1(self, ths_code: str) -> Response:
        """获取3秒 tick 成交数据。

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头。

        Returns:
            Response: 包含成交数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效。
            ValueError: 如果开始时间戳大于或等于结束时间戳。
        """
        ths_code = ths_code.upper()
        if len(ths_code) != 10 or not any(ths_code.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 开头")

        params = {
            "code": ths_code,
        }

        return self.call(method="tick.level1", params=params)

    def tick_super_level1(self, ths_code: str, date: Optional[str] = None,
                          buffer_size: int = 1024 * 1024 * 2) -> Response:
        """获取3秒超级盘口数据（包含委托档位）。

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头。
            date (Optional[str]): 查询历史日期字符串，近一年，格式为 'YYYYMMDD'。


        Returns:
            Response: 包含超级盘口数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效。
            ValueError: 如果开始时间戳大于或等于结束时间戳。
        """
        ths_code = ths_code.upper()
        if len(ths_code) != 10 or not any(ths_code.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 开头")

        if date:
            try:
                datetime.strptime(date, "%Y%m%d")
            except ValueError:
                return error_response("日期格式无效，必须为 'YYYYMMDD'")

        params = {
            "code": ths_code,
            "date": date,
        }

        print(params)

        return self.call(method="tick.super_level1", params=params, buffer_size=buffer_size)

    def ths_industry(self) -> Response:
        """获取行业板块数据。

        Returns:
            Response: 包含行业板块数据的响应对象。
        """
        return self.block_data(0xCE5F)

    def ths_concept(self) -> Response:
        """获取概念板块数据。

        Returns:
            Response: 包含概念板块数据的响应对象。
        """
        return self.block_data(0xCE5E)

    def forex_list(self) -> Response:
        """基本汇率。

        Returns:
            Response: 。
        """
        return self.market_block("UFXB")

    def index_list(self) -> Response:
        """获取指数板块数据。

        Returns:
            Response: 包含指数板块数据的响应对象。
        """
        return self.block_data(0xD2)

    def stock_cn_lists(self):
        """A股"""
        return self.block_data(0xE)

    def stock_us_lists(self):
        """美股"""
        return self.block_data(0xDC47)

    def stock_hk_lists(self):
        """港股"""
        return self.block_data(0xB)

    def stock_bj_lists(self):
        """北交所"""
        return self.block_data(0xCA8B)

    def stock_uk_lists(self):
        """英国"""
        return self.market_block("UEUA")

    def stock_b_lists(self):
        """B股"""
        return self.block_data(0xF)

    def futures_lists(self):
        """主力合约"""
        return self.block_data(0xCAE0)

    def option_lists(self):
        pass

    def nasdaq_lists(self):
        """纳斯达克"""
        return self.block_data(0xD9A9)

    def bond_lists(self) -> Response:
        """可转债"""
        return self.block_data(0xCE14)

    def fund_etf_lists(self) -> Response:
        """ETF基金"""
        return self.block_data(0xCFF3)

    def fund_etf_t0_lists(self) -> Response:
        """ETF T+0基金"""
        return self.block_data(0xD90C)

    def depth(self, ths_code: Union[str, list]) -> Response:
        """获取深度数据 5档。

        Returns:
            Response: 包含深度数据的响应对象。
        """
        params = {
            "codes" if isinstance(ths_code, list) else "code": ths_code,
        }

        response = self.call(method="depth", params=params)
        return response

    def call_auction(self, ths_code: str) -> Response:
        """早盘集合竞价

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA','USZA','USHD','USZD' 等开头。

        Returns:
            Response:
        """
        ths_code = ths_code.upper()
        if len(ths_code) != 10 or not any(ths_code.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 等开头")

        params = {
            "code": ths_code,
        }

        response = self.call(method="call_auction", params=params)

        return response

    def call_auction_anomaly(self, market: str = "USHA") -> Response:
        """竞价异动

        Args:
            market (str): 市场， 'USHA','USZA'

        Returns:
            Response:
        """
        market = market.upper()
        if len(market) != 4 or not any(market.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为4个字符，且以 'USHA' 或 'USZA' 等开头")

        params = {
            "market": market,
        }

        response = self.call(method="call_auction_anomaly", params=params)

        if response.payload.result and isinstance(response.payload.result, list):
            ydkey = "异动类型1"
            for entry in response.payload.result:
                if isinstance(entry, dict) and ydkey in entry:
                    entry[ydkey] = CALL_AUCTION_ANOMALY_MAP.get(entry[ydkey], entry[ydkey])

        return response

    def corporate_action(self, ths_code: str) -> Response:
        """权息资料

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA','USZA' 等开头。

        Returns:
            Response:
        """
        ths_code = ths_code.upper()
        if len(ths_code) != 10 or not any(ths_code.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 等开头")

        params = {
            "code": ths_code,
        }

        response = self.call(method="corporate_action", params=params)

        return response

    def klines(self, ths_code: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
               adjust: str = "", interval: str = "day",
               count: int = -1) -> Response:
        """获取 K 线数据。

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头。
            start_time (datetime, optional): 开始时间。
            end_time (datetime, optional): 结束时间。
            adjust (str, optional): 复权类型，默认为 ""。参数支持: 前复权:"forward",后复权:"backward",不复权:""
            interval (str, optional): k线周期类型，默认为 "day"。参数支持: 1分钟:"1m",5分钟:"5m",15分钟:"15m",30分钟:"30m",60分钟:"60m",120分钟:"120m",日:"day",周:"week",月:"month",季:"quarter",年:"year",
            count (int, optional): 数据条数，优先于 start/end，count有数据时候start_time,end_time则无效 默认为 -1。

        Returns:
            Response: 包含 K 线数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效。
            ValueError: 如果复权类型、周期类型无效，或 start/end 类型不一致。
        """

        # 强制执行 count 与 start_time/end_time 的互斥性
        if count != -1 and (start_time is not None or end_time is not None):
            raise ValueError("'count' 参数不能与 'start_time' 或 'end_time' 同时使用。")
        if count == -1 and start_time is None and end_time is None:
            raise ValueError("必须提供 'count' 或同时提供 'start_time' 和 'end_time'。")

        # 对 start_time 和 end_time 的一致性进行额外验证
        if (start_time is not None and end_time is None) or (start_time is None and end_time is not None):
            raise ValueError("'start_time' 和 'end_time' 必须同时提供或都不提供。")

        ths_code = ths_code.upper()
        if len(ths_code) != 10 or not any(ths_code.upper().startswith(market) for market in MARKETS):
            return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 开头")
        if adjust not in ["forward", "backward", ""]:
            return error_response(f"无效的复权类型: {adjust}")
        if interval not in ["1m", "5m", "15m", "30m", "60m", "120m", "day", "week", "month", "quarter", "year"]:
            return error_response(f"无效的周期类型: {interval}")

        params = {
            "code": ths_code,
            "adjust": adjust,
            "interval": interval,
        }
        if count > 0:
            params["count"] = count
        else:
            if start_time is not None:
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=tz)
                params["start_time"] = start_time.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')

            if end_time is not None:
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=tz)
                params["end_time"] = end_time.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')

        response = self.call(method="klines", params=params)
        if response.err_info == "":
            if interval in ["1m", "5m", "15m", "30m", "60m", "120m"]:
                for entry in response.get_result():
                    if "时间" in entry:
                        entry["时间"] = _int2time(int(entry["时间"]))
            else:
                for entry in response.get_result():
                    if "时间" in entry:
                        entry["时间"] = datetime.strptime(str(entry["时间"]), "%Y%m%d")
        return response

    def wencai_base(self, condition: str) -> Response:
        """问财基础查询。

        Args:
            condition (str): 查询条件，如 "所属行业"。

        Returns:
            Response: 包含查询结果的响应对象。
        """
        return self.call("wencai_base", condition)

    def wencai_nlp(self, condition: str) -> Response:
        """问财自然语言处理查询。

        Args:
            condition (str): 查询条件，如 "涨停;所属行业;所属概念;热度排名;流通市值"。

        Returns:
            Response: 包含查询结果的响应对象。
        """
        return self.call("wencai_nlp", condition, buffer_size=1024 * 1024 * 8)

    def order_book_ask(self, ths_code: str) -> Response:
        """获取市场深度卖方数据。

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头。

        Returns:
            Response: 包含卖方数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效。
        """
        return self.call("order_book_ask", ths_code, buffer_size=1024 * 1024 * 8)

    def order_book_bid(self, ths_code: str) -> Response:
        """获取市场深度买方数据。

        Args:
            ths_code (str): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头。

        Returns:
            Response: 包含买方数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效。
        """
        return self.call("order_book_bid", ths_code, buffer_size=1024 * 1024 * 8)

    def market_data_block(self, block_code: Any, query_key: str = "基础数据") -> Response:
        """获取板块市场数据。

        Args:
            block_code (str or List[str]): 板块，格式为10位，

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "55,38,39,13,19,92,90,5,275,276,277"},

            "扩展": {"id": 202, "data_type": "3934664,199112,68285,592890,1771976,3250,3251,3252"},
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        if isinstance(block_code, str):
            block_code = [block_code]
        elif not isinstance(block_code, list) or not all(isinstance(code, str) for code in block_code):
            return error_response("block_code 必须是字符串或者字符串列表")

        for code in block_code:
            code = code.upper()
            if len(code) != 10 or not any(code.upper().startswith(market) for market in BLOCK_MARKETS):
                return error_response("板块代码必须为10个字符")

        markets = {code[:4] for code in block_code}
        if len(markets) > 1:
            return error_response("一次性查询多支股票必须市场代码相同")

        market = markets.pop()
        short_codes = ",".join([code[4:] for code in block_code])
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,
            "market": market,
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"
        }
        return self.query_data(params)

    def market_data_cn(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """获取股票市场数据。

        Args:
            ths_code (str or List[str]): 证券代码，格式为10位，以 'USHA' 或 'USZA' 开头，可为单个代码或代码列表。

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """

        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,48,13,49,7,6,8,9,19,18,12"},
            "基础数据2": {"id": 200, "data_type": "5,55,10,48,49,13,19,6,12"},
            "基础数据3": {"id": 200, "data_type": "5,55,10,6"},

            "扩展1": {"id": 202, "data_type": "199112,592888,592890,264648,1968584,526792,1771976,3153,2947,2427336"},
            "扩展2": {"id": 202,
                      "data_type": "199112,264648,592888,592890,1968584,3541450,461256,1771976,3153,3475914"},

            "汇总": {"id": 202,
                     "data_type": "5,6,8,9,10,12,13,402,19,407,24,30,48,49,69,70,3250,920371,55,199112,264648,1968584,461256,1771976,3475914,3541450,526792,3153,592888,592890"},
        }
        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或者字符串列表")

        for code in ths_code:
            code = code.upper()
            if len(code) != 10 or not any(code.upper().startswith(market) for market in MARKETS):
                return error_response("证券代码必须为10个字符，且以 'USHA' 或 'USZA' 开头")

        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("一次性查询多支股票必须市场代码相同")

        market = markets.pop()
        short_codes = ",".join([code[4:] for code in ths_code])
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,
            "market": market,
            "datatype": config["data_type"],  # 数据类型
            "service": "zhu"
        }
        return self.query_data(params)

    def market_data_us(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """us股票市场数据。

        Args:
            ths_code (str or List[str]): 证券代码，格式为10位，以 'UNQQ' 或 'UNQS' 开头，可为单个代码或代码列表。

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """

        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,7,6,8,9,13,25,24,49,30,31,95,96,12"},
            "每股净资产": {"id": 201, "data_type": "1005"},
            "每股收益": {"id": 201, "data_type": "1002"},
            "净利润": {"id": 201, "data_type": "1566"},
            "财务指标": {"id": 202, "data_type": "199112,264648,3541450,3153,2947,526792"}
        }
        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或者字符串列表")

        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.upper().startswith(market) for market in MARKETS):
                return error_response("证券代码必须为10个字符，且以 'UNQQ' 或 'UNQS' 开头")

        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("一次性查询多支股票必须市场代码相同")

        market = markets.pop()
        short_codes = ",".join([code[4:] for code in ths_code])
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        # data_type = "5,55,10,7,6,8,9,13,25,24,49,30,31,95,96,12"

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,
            "market": market,
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"
        }
        return self.query_data(params)

    def market_data_hk(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """获取香港股票市场数据，根据指定的查询键选择数据类型。

        Args:
            ths_code (str or List[str]): 证券代码，格式为10位，以 'UNQQ' 或 'UNQS' 开头。
                                        可为单个代码或代码列表。
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,13,19,6,7,8,9"},
            "每股净资产": {"id": 201, "data_type": "1005"},
            "净利润": {"id": 201, "data_type": "619"},
            "财务指标": {"id": 202, "data_type": "199112,264648,3153,2947,3541450"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_uk(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """英国市场

        Args:
            ths_code (str or List[str]):
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response:

        Raises:
            InvalidCodeError:
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,7,6,8,9,13,25,24,49,30,31,95,96,12"},
            "每股净资产": {"id": 201, "data_type": "1005"},
            "每股收益": {"id": 201, "data_type": "1002"},
            "净利润": {"id": 201, "data_type": "1566"},
            "扩展": {"id": 202, "data_type": "199112,264648,3541450,3153,2947,526792"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_bond(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """债

        Args:
            ths_code (str or List[str]):
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response:

        Raises:
            InvalidCodeError:
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,80,49,13,19,25,31,24,30,6,7,8,9,12"},
            "利率": {"id": 201, "data_type": "1322"},
            "扩展": {"id": 202, "data_type": "199112,264648"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_fund(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """基金ETF

        Args:
            ths_code (str or List[str]):
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response:

        Raises:
            InvalidCodeError:
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,48,13,49,12,7,6,8,9,24,30,25,31,19,18,14"},
            "净值": {"id": 201, "data_type": "3397"},
            "扩展": {"id": 202, "data_type": "1968584,2427336,2820564,1771976,461256,526792"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_future(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """期货

        Args:
            ths_code (str or List[str]):
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response:

        Raises:
            InvalidCodeError:
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,24,30,25,31,49,13,65,71,8,9,7,6,66,72,14,15,19,12"},
            "日增仓": {"id": 202, "data_type": "133964"},
            "扩展": {"id": 202, "data_type": "3082712,264648,526792"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_forex(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """汇率市场数据

        Args:
            ths_code (str or List[str]): 代码
            query_key (str):

        Returns:
            Response: 包含股票市场数据的响应对象。

        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,20,21,8,9,7,18,6"},

            "扩展": {"id": 202, "data_type": "264648,526792,199112"},
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response(f"证券代码必须至少4个字符，且以有效市场代码开头 {code[:4]}")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def market_data_index(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """获取指数数据

        Args:
            ths_code (str or List[str]): 证券代码，格式为10位，以 'USHI' 或 'USZI' 开头。
                                        可为单个代码或代码列表。
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """
        # 查询键配置字典，映射查询键到对应的ID和数据类型
        QUERY_CONFIG = {
            "基础数据": {"id": 200, "data_type": "5,55,10,13,49,7,8,9,19,6,12"},
            "扩展": {"id": 202, "data_type": "199112,264648,1771976,526792"}
        }

        # 验证查询键是否有效
        if query_key not in QUERY_CONFIG:
            return error_response(f"无效的查询键。必须为 {list(QUERY_CONFIG.keys())} 之一")

        # 将单一字符串转换为列表以统一处理
        if isinstance(ths_code, str):
            ths_code = [ths_code]
        elif not isinstance(ths_code, list) or not all(isinstance(code, str) for code in ths_code):
            return error_response("ths_code 必须是字符串或字符串列表")

        # 验证证券代码格式
        for code in ths_code:
            code = code.upper()
            if len(code) < 4 or not any(code.startswith(market) for market in MARKETS):
                return error_response("证券代码必须至少4个字符，且以有效市场代码开头")

        # 检查市场代码是否一致
        markets = {code[:4] for code in ths_code}
        if len(markets) > 1:
            return error_response("所有股票代码必须属于同一市场")

        # 准备查询参数
        market = markets.pop()  # 获取唯一的市场代码
        short_codes = ",".join([code[4:] for code in ths_code])  # 提取短代码并用逗号连接
        config = QUERY_CONFIG[query_key]  # 获取查询键对应的配置

        params = {
            "id": config["id"],  # 查询ID
            "codelist": short_codes,  # 短代码列表
            "market": market,  # 市场代码
            "datatype": config["data_type"],  # 数据类型
            "service": "fu"  # 服务标识
        }

        return self.query_data(params)  # 调用查询方法并返回结果

    def option_data(self, ths_code: Any, query_key: str = "基础数据") -> Response:
        """todo 期权数据

        Args:
            ths_code (str or List[str]): 证券代码，格式为10位，以 'UNQQ' 或 'UNQS' 开头。
                                        可为单个代码或代码列表。
            query_key (str): 查询键，用于选择数据类型和ID配置。可选值：
                             - 'default': 数据类型 5,55,10,13,19,6,7,8,9 (ID 200)
                             - '每股净资产': 数据类型 1005 (ID 201)
                             - '净利润': 数据类型 619 (ID 201)
                             - 'type2': 数据类型 199112,264648,3153,2947,3541450 (ID 202)

        Returns:
            Response: 包含股票市场数据的响应对象。

        Raises:
            InvalidCodeError: 如果证券代码格式无效或多个代码的市场不一致。
        """
        pass

    def ipo_today(self) -> Response:
        """查询今日 IPO 数据。

        Returns:
            Response: 包含今日 IPO 数据的响应对象。
        """
        return self.call("ipo_today")

    def ipo_wait(self) -> Response:
        """查询待申购 IPO 数据。

        Returns:
            Response: 包含待申购 IPO 数据的响应对象。
        """
        return self.call("ipo_wait")

    def normalize_symbol(self, ths_code: Union[str, list]) -> Response:
        """补齐完整代码，补齐完整市场代码

        Returns:
            Response:
        """
        params = {
            "codes" if isinstance(ths_code, list) else "code": ths_code,
        }

        response = self.call(method="complete_code", params=params)
        return response

    def watchlist(self, cookie: str = "") -> Response:
        """自选股

        :param cookie: 在浏览器直接复制完整全部cookie
        :return:
        """

        params = {
            "cookie": cookie,
        }

        response = self.call(method="watchlist", params=params)
        return response

    def watchlist_add(self, cookie: str = "", code: str = "") -> Response:
        """添加自选。
            :param cookie: 在浏览器直接复制完整全部cookie
            :param code: 证券代码，格式为6位。e.g. 300033
        """
        params = {
            "cookie": cookie,
            "code": code,
            "method": "add",
        }

        response = self.call(method="watchlist", params=params)
        return response

    def watchlist_delete(self, cookie: str = "", code: str = "", marketid: str = "") -> Response:
        """删除自选。
            :param cookie: 在浏览器直接复制完整全部cookie
            :param code: 证券代码，格式为6位。e.g. 300033
            :param marketid: 市场代码，格式为4位。e.g. 33
        """
        params = {
            "cookie": cookie,
            "code": code,
            "marketid": marketid,
            "method": "delete",
        }

        response = self.call(method="watchlist", params=params)
        return response

    def group(self, cookie: str = "") -> Response:
        """分组

        :param cookie: 在浏览器直接复制完整全部cookie
        :return:
        """

        params = {
            "cookie": cookie,
        }

        response = self.call(method="group", params=params)
        return response

    def group_new(self, cookie: str, group_name: str, version: str) -> Response:
        """新建分组

        :param cookie: 在浏览器直接复制完整全部cookie
        :param group_name: 分组名称
        :param version: 版本号
        :return:
        """

        params = {
            "cookie": cookie,
            "method": "group_new",
            "from": "sjcg_ios",
            "name": group_name,
            "type": 0,
            "version": version
        }

        response = self.call(method="group", params=params)
        return response

    def group_delete(self, cookie: str, ids: str, version: str) -> Response:
        """删除分组

        :param cookie: 在浏览器直接复制完整全部cookie
        :param ids: 分组ID，多个用逗号分隔
        :param version: 版本号
        :return:
        """

        params = {
            "cookie": cookie,
            "method": "group_delete",
            "from": "sjcg_ios",
            "ids": ids,
            "version": version
        }

        response = self.call(method="group", params=params)
        return response

    def group_code_add(self, cookie: str, id: str, version: str, ths_codes: List[str]) -> Response:
        """分组添加元素

        :param cookie: 在浏览器直接复制完整全部cookie
        :param id: 分组ID
        :param version: 版本号
        :param ths_codes: 证券代码列表，格式为10位，以 'USHA' 或 'USZA' 开头。
        :return:
        """
        num = 0

        codes = []
        market_ids = []

        for ths_code in ths_codes:
            if len(ths_code) <= 4:
                print(f"ths_code {ths_code} 必须为大于4位")
                continue
            if ths_code[:4] not in ["USHA", "USZA", "USHD", "USZD", "USTM"]:
                print(f"ths_code {ths_code} 必须以有效市场代码开头")
                continue

            codes.append(ths_code[4:].upper())
            market_ids.append(market_to_market_id(ths_code[:4].upper()))
            num += 1

        content = f"{'|'.join(codes)}|,{'|'.join(market_ids)}|"

        params = {
            "cookie": cookie,
            "method": "group_content_add",
            "from": "sjcg_ios",
            "id": id,
            "content": content,
            "num": num,
            "add_mode": "prepend",
            "version": version
        }

        response = self.call(method="group", params=params)
        return response

    def group_code_delete(self, cookie: str, id: str, version: str, ths_codes: List[str]) -> Response:
        """删除分组

        :param cookie: 在浏览器直接复制完整全部cookie
        :param id: 分组ID
        :param version: 版本号
        :param ths_codes: 证券代码列表，格式为10位，以 'USHA' 或 'USZA' 开头。
        :return:
        """

        num = 0
        codes = []
        market_ids = []

        for ths_code in ths_codes:
            if len(ths_code) <= 4:
                print(f"ths_code {ths_code} 必须为大于4位")
                continue
            if ths_code[:4] not in ["USHA", "USZA", "USHD", "USZD", "USTM"]:
                print(f"ths_code {ths_code} 必须以有效市场代码开头")
                continue

            codes.append(ths_code[4:].upper())
            market_ids.append(market_to_market_id(ths_code[:4].upper()))
            num += 1

        content = f"{'|'.join(codes)}|,{'|'.join(market_ids)}|"

        params = {
            "cookie": cookie,
            "method": "group_content_delete",
            "from": "sjcg_ios",
            "id": id,
            "content": content,
            "num": num,
            "version": version
        }

        response = self.call(method="group", params=params)
        return response

    def help(self, req: str = "") -> str:
        """获取帮助信息。

        Args:
            req (str, optional): 查询条件，如 "about,doc"。默认为空字符串。

        Returns:
            str: 帮助信息字符串。
        """
        result_code, result = self.lib_call("help", req)
        response = Response(result)
        payload_result = response.get_result()

        if isinstance(payload_result, str):
            return payload_result
        elif isinstance(payload_result, dict):
            help_value = payload_result.get("help", "")
            return help_value if isinstance(help_value, str) else ""
        return ""
