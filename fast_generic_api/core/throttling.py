# -*- coding: utf-8 -*-
# @FileName: throttling.py
# @Software: PyCharm
"""轻量节流接口（进程内内存实现，生产可换 Redis 后端）。"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request


class BaseThrottle:
    """节流基类。"""

    async def allow_request(self, request: Request) -> bool:
        return True

    def get_ident(self, request: Request) -> str:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "id", None) is not None:
            return f"user:{user.id}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"


class SimpleRateThrottle(BaseThrottle):
    """固定窗口：``rate`` 次 / ``period`` 秒。"""

    rate: int = 60
    period: float = 60.0
    scope: str = "default"

    _hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def allow_request(self, request: Request) -> bool:
        key = f"{self.scope}:{self.get_ident(request)}"
        now = time.monotonic()
        window_start = now - self.period
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= self.rate:
            return False
        bucket.append(now)
        return True


class AnonRateThrottle(SimpleRateThrottle):
    """匿名客户端默认限流。"""

    rate = 30
    period = 60.0
    scope = "anon"
