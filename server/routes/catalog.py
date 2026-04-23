# encoding: utf-8
from fastapi import APIRouter, Query

from ..connection import connection, _response_to_dict

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

LIST_METHODS = {
    "industry": "ths_industry",
    "concept": "ths_concept",
    "stock-cn": "stock_cn_lists",
    "stock-us": "stock_us_lists",
    "stock-hk": "stock_hk_lists",
    "index-list": "index_list",
}


@router.get("/{list_type}")
async def list_data(list_type: str):
    method_name = LIST_METHODS.get(list_type)
    if not method_name:
        return {"success": False, "error": f"不支持的列表类型: {list_type}", "data": None}

    def _query(ths):
        import time
        started = time.perf_counter()
        resp = getattr(ths, method_name)()
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/block-constituents")
async def block_constituents(
    link_code: str = Query(..., description="板块代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.block_constituents(link_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
