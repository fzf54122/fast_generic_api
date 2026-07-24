# -*- coding: utf-8 -*-
# @FileName: tortoise_orm.py
# @Software: PyCharm
"""Tortoise ORM Backend 实现。"""
from contextlib import asynccontextmanager
from typing import Any

from tortoise.transactions import in_transaction

from fast_generic_api.backends.base import BaseBackend


class TortoiseBackend(BaseBackend):
    """Tortoise ORM 适配器。"""

    # ------------------------------------------------------------------
    # 查询集构建
    # ------------------------------------------------------------------
    def get_queryset(self, model: Any):
        return model.all()

    def filter(self, queryset, **kwargs):
        return queryset.filter(**kwargs)

    def order_by(self, queryset, *fields: str):
        return queryset.order_by(*fields)

    def select_related(self, queryset, *fields: str):
        return queryset.select_related(*fields)

    def prefetch_related(self, queryset, *fields: str):
        return queryset.prefetch_related(*fields)

    def offset_limit(self, queryset, offset: int, limit: int):
        return queryset.offset(offset).limit(limit)

    def search(self, queryset, fields: list[str], term: str):
        if not term or not fields:
            return queryset
        from tortoise.expressions import Q

        query = Q()
        for field_name in fields:
            query |= Q(**{f"{field_name}__icontains": term})
        return queryset.filter(query)

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------
    async def count(self, queryset) -> int:
        return await queryset.count()

    async def first(self, queryset):
        return await queryset.first()

    async def all(self, queryset) -> list:
        return await queryset

    # ------------------------------------------------------------------
    # 写操作
    # ------------------------------------------------------------------
    async def create(self, model: Any, **kwargs):
        return await model.create(**kwargs)

    async def save(self, instance) -> None:
        await instance.save()

    async def update_from_dict(self, instance, data: dict) -> None:
        await instance.update_from_dict(data).save()

    async def delete(self, instance) -> None:
        await instance.delete()

    # ------------------------------------------------------------------
    # 元信息
    # ------------------------------------------------------------------
    def resolve_model(self, queryset_or_model: Any) -> Any:
        # QuerySet 有 .model 属性，Model 类本身没有
        model = getattr(queryset_or_model, "model", None)
        return model if model is not None else queryset_or_model

    def get_model_meta(self, model: Any):
        return getattr(model, "_meta", None)

    # ------------------------------------------------------------------
    # 事务
    # ------------------------------------------------------------------
    @asynccontextmanager
    async def in_transaction(self):
        async with in_transaction():
            yield


# 默认单例，避免每个请求重复构造
tortoise_backend = TortoiseBackend()
