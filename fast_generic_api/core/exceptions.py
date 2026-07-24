# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午1:50
# @Author  : fzf
# @FileName: exceptions.py
# @Software: PyCharm
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fast_generic_api.core.response import Response


class FastAutoException(Exception):
    """框架基础异常，子类定义 status_code 与 detail"""
    status_code = 500
    code = 50000
    detail = "基础错误"


class HTTPException(FastAutoException):
    status_code = 404
    code = 40400
    detail = "Object not found"


class HTTPPermissionException(FastAutoException):
    status_code = 403
    code = 40300
    detail = "Permission denied"


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
