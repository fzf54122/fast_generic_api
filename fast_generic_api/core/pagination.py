# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午1:21
# @Author  : fzf
# @FileName: pagination.py
# @Software: PyCharm
from fastapi import Request

from fast_generic_api.backends import tortoise_backend


class LimitOffsetPagination:
    default_limit = 10
    max_limit = 1000

    @classmethod
    def get_limit_offset(cls, request: Request):
        """从 query params 获取 limit 和 offset"""
        limit = request.query_params.get("limit")
        offset = request.query_params.get("offset")

        limit = int(limit) if limit and limit.isdigit() else cls.default_limit
        offset = int(offset) if offset and offset.isdigit() else 0

        limit = min(limit, cls.max_limit)
        return limit, offset

    @classmethod
    async def get_paginated_response(cls, request: Request, queryset, serializer_fn, backend=None):
        """执行分页，返回统一结构 dict"""
        backend = backend or tortoise_backend

        # 如果传进来的是 list，说明上游传错了，直接返回全部
        if isinstance(queryset, list):
            return {
                "total": len(queryset),
                "limit": len(queryset),
                "offset": 0,
                "results": serializer_fn(queryset, many=True),
            }

        limit, offset = cls.get_limit_offset(request)
        total = await backend.count(queryset)
        objs = await backend.all(backend.offset_limit(queryset, offset, limit))
        data = serializer_fn(objs, many=True)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": data,
        }


class PageNumberPagination:
    """page / page_size 风格分页"""
    default_page_size = 10
    max_page_size = 1000

    @classmethod
    def get_page_params(cls, request: Request):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")

        page = int(page) if page and page.isdigit() else 1
        page_size = int(page_size) if page_size and page_size.isdigit() else cls.default_page_size
        page_size = min(page_size, cls.max_page_size)
        return page, page_size

    @classmethod
    async def get_paginated_response(cls, request: Request, queryset, serializer_fn, backend=None):
        backend = backend or tortoise_backend

        if isinstance(queryset, list):
            return {
                "total": len(queryset),
                "page": 1,
                "page_size": len(queryset),
                "results": serializer_fn(queryset, many=True),
            }

        page, page_size = cls.get_page_params(request)
        total = await backend.count(queryset)
        offset = (page - 1) * page_size
        objs = await backend.all(backend.offset_limit(queryset, offset, page_size))
        data = serializer_fn(objs, many=True)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": data,
        }
