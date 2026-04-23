# encoding: utf-8
from fastapi import APIRouter, Query

from ..connection import connection, _response_to_dict

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/search")
async def search(
    pattern: str = Query(..., description="搜索关键词"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.search_symbols(pattern)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/complete-code")
async def complete_code(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.complete_ths_code(ths_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/news")
async def news(
    code: str = Query("1A0001", description="新闻代码"),
    market: str = Query("USHI", description="市场代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.news(code=code, market=market)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/ipo/today")
async def ipo_today():
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.ipo_today()
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
