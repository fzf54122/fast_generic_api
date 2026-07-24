# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:50
# @Author  : fzf
# @FileName: response.py
# @Software: PyCharm
from typing import Any, Generic, List, Optional, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """OpenAPI 可见的统一响应信封（与 ``Response`` JSON 结构对齐）。"""

    code: int = 200
    status: str = "success"
    data: Optional[T] = None
    msg: Optional[str] = "OK"


class PaginatedData(BaseModel, Generic[T]):
    """分页 data 载荷（LimitOffset / PageNumber 共用字段子集）。"""

    total: int = 0
    results: List[T] = Field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


def envelope_model(data_type: Type[Any] | None, *, many: bool = False, paginated: bool = False):
    """为路由生成 OpenAPI response_model（信封 + 可选分页）。"""
    if data_type is None:
        return Envelope[Any]
    if paginated:
        return Envelope[PaginatedData[data_type]]
    if many:
        return Envelope[List[data_type]]
    return Envelope[data_type]


class Response(JSONResponse):
    """
    通用响应类：
    - 成功返回: Response(data=..., msg=..., code=200)
    - 分页返回: Response(data={"total":..., "results":...}) 或 Response(data=..., total=...)
    - 失败返回: Response(data=..., code=400, status='error', msg=...)

    注意：业务码 code 放入响应体，HTTP status_code 默认 200。
    若需要返回非 2xx HTTP 状态（如 201/404/403），请通过 status_code 显式指定。
    """

    def __init__(
        self,
        data: Any | None = None,
        code: int = 200,
        status: str = "success",
        msg: str | None = "OK",
        status_code: int = 200,
        total: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        **kwargs,
    ):
        data = jsonable_encoder(data)
        content = {"code": code, "status": status, "data": data, "msg": msg}

        if total is not None:
            content["total"] = total
        if page is not None:
            content["page"] = page
        if page_size is not None:
            content["page_size"] = page_size

        content.update(kwargs)
        super().__init__(content=content, status_code=status_code)
