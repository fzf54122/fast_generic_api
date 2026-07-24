# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午1:50
# @Author  : fzf
# @FileName: exceptions.py
# @Software: PyCharm
"""框架异常与统一错误码。

业务码分段约定（响应体 ``code`` 字段，与 HTTP status 分离）：

- 2xxxx  成功（当前成功统一用 200）
- 4xxxx  客户端错误
  - 40000  请求参数/业务校验失败
  - 40300  权限不足
  - 40400  资源不存在
  - 42200  请求体/查询参数 schema 校验失败（Pydantic）
- 5xxxx  服务端错误
  - 50000  未分类服务端错误
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fast_generic_api.core.response import Response


class FastAutoException(Exception):
    """框架基础异常，子类定义 status_code 与 detail"""

    status_code = 500
    code = 50000
    detail = "基础错误"

    def __init__(self, detail: str | None = None, *, code: int | None = None, status_code: int | None = None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class HTTPException(FastAutoException):
    status_code = 404
    code = 40400
    detail = "Object not found"


class HTTPPermissionException(FastAutoException):
    status_code = 403
    code = 40300
    detail = "Permission denied"


class HTTPBadRequestException(FastAutoException):
    status_code = 400
    code = 40000
    detail = "Bad request"


async def fast_auto_exception_handler(request: Request, exc: FastAutoException) -> JSONResponse:
    """统一异常处理器：把框架异常转成标准响应信封"""
    return Response(
        data=None,
        code=exc.code,
        status="error",
        msg=exc.detail,
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求体/查询参数校验失败 → 统一信封（业务码 42200）。"""
    return Response(
        data=exc.errors(),
        code=42200,
        status="error",
        msg="Validation error",
        status_code=422,
    )


def register_exception_handlers(app) -> None:
    """在 FastAPI 应用上注册框架异常处理器"""
    app.add_exception_handler(FastAutoException, fast_auto_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
