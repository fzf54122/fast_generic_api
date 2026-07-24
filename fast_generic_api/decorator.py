# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午3:46
# @Author  : fzf
# @FileName: decorator.py
# @Software: PyCharm
from typing import List, Optional


def api_meta(summary: str = None, description: str = None,
             tags: list = None, responses: dict = None):
    """为 endpoint 注入 OpenAPI 元信息"""
    def decorator(func):
        if summary:
            setattr(func, "_summary", summary)
        if description:
            setattr(func, "_description", description)
        if tags:
            setattr(func, "_tags", tags)
        if responses:
            setattr(func, "_responses", responses)
        return func
    return decorator


def action(detail: bool = False, methods: Optional[List[str]] = None,
           url_path: Optional[str] = None, response_model=None):
    """自定义 action 装饰器（对齐 DRF）。

    :param detail: True → /{prefix}/{lookup}/{url_path}/；False → /{prefix}/{url_path}/
    :param methods: HTTP 方法列表，默认 ["GET"]
    :param url_path: 路径段，默认取方法名（下划线转横线）
    :param response_model: 可选 OpenAPI 响应模型
    """
    def decorator(func):
        setattr(func, "_action_meta", {
            "detail": detail,
            "methods": methods or ["GET"],
            "url_path": url_path,
            "response_model": response_model,
        })
        return func
    return decorator
