# encoding: utf-8
from fastapi import APIRouter, Query

from ..connection import connection, _response_to_dict

router = APIRouter(prefix="/api/market", tags=["market"])

MARKET_METHODS = {
    "cn": "market_data_cn",
    "us": "market_data_us",
    "hk": "market_data_hk",
    "index": "market_data_index",
    "block": "market_data_block",
    "future": "market_data_future",
    "forex": "market_data_forex",
}


@router.get("/{market}")
async def market_data(
    market: str,
    codes: str = Query(..., description="逗号分隔的证券代码"),
    query_key: str = Query("基础数据", description="查询键"),
):
    method_name = MARKET_METHODS.get(market)
    if not method_name:
        return {"success": False, "error": f"不支持的市场: {market}", "data": None}

    code_list = [c.strip() for c in codes.split(",") if c.strip()]

    def _query(ths):
        import time
        started = time.perf_counter()
        resp = getattr(ths, method_name)(code_list if len(code_list) > 1 else code_list[0], query_key=query_key)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
