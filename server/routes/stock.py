# encoding: utf-8
from fastapi import APIRouter, Query

from ..connection import connection, _response_to_dict

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("/klines")
async def klines(
    ths_code: str = Query(..., description="证券代码"),
    count: int = Query(100, description="K线数量"),
    interval: str = Query("day", description="K线周期"),
    adjust: str = Query("", description="复权方式"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.klines(ths_code, count=count, interval=interval, adjust=adjust)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/intraday")
async def intraday(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.intraday_data(ths_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/depth")
async def depth(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.depth(ths_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/big-order-flow")
async def big_order_flow(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.big_order_flow(ths_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}


@router.get("/call-auction")
async def call_auction(
    ths_code: str = Query(..., description="证券代码"),
):
    def _query(ths):
        import time
        started = time.perf_counter()
        resp = ths.call_auction(ths_code)
        duration = round((time.perf_counter() - started) * 1000, 2)
        return _response_to_dict(resp), {}, {"sdk_duration_ms": duration}

    try:
        raw_payload, _, timing = connection.execute(_query)
        raw_payload["timing"] = timing
        return raw_payload
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
