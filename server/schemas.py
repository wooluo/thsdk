# encoding: utf-8
from typing import Optional

from fastapi import Query


class MarketQuery:
    def __init__(
        self,
        codes: str = Query(..., description="逗号分隔的证券代码"),
        query_key: str = Query("基础数据", description="查询键"),
    ):
        self.codes = [c.strip() for c in codes.split(",") if c.strip()]
        self.query_key = query_key


class KlineQuery:
    def __init__(
        self,
        ths_code: str = Query(..., description="证券代码"),
        count: int = Query(100, description="K线数量"),
        interval: str = Query("day", description="K线周期: 1m/5m/15m/30m/60m/day/week/month"),
        adjust: str = Query("", description="复权: 空/forward/backward"),
    ):
        self.ths_code = ths_code
        self.count = count
        self.interval = interval
        self.adjust = adjust
