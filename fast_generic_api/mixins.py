# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:49
# @Author  : fzf
# @FileName: mixins.py
# @Software: PyCharm
from typing import Any, Optional
from fastapi import Request, Body
from fast_generic_api.core import status
from fast_generic_api.core.response import Response


class BaseMixin:
    """提供通用工具方法"""

    def _get_lookup_kwargs(self, pk: Any) -> dict:
        lookup_field = self.lookup_url_kwarg or self.lookup_field
        return {lookup_field: pk}


class CreateModelMixin(BaseMixin):
    action = "create"

    async def create(self, data: Any = Body(...)) -> Response:
        """通用创建方法"""
        data_dict = self.serialize_input_data(data)
        obj = await self.queryset.create(**data_dict)
        serializer = self.get_serializer(obj)
        return Response(serializer)


class ListModelMixin(BaseMixin):
    action = "list"

    async def list(self, request: Request) -> Response:
        """获取对象列表，支持过滤、排序和分页"""
        qs = self.get_queryset()
        if self.ordering:
            qs = qs.order_by(*self.ordering)
        if self.filter_class:
            qs = self.filter_class(request, qs)
        if self.pagination_class:
            return Response(await self.pagination_class.get_paginated_response(request, qs, self.get_serializer))
        serializer = self.get_serializer(await qs, many=True)
        return Response(serializer)


class RetrieveModelMixin(BaseMixin):
    action = "retrieve"

    async def retrieve(self, request: Request, pk: Any) -> Response:
        """获取单个对象"""
        self.kwargs.update(self._get_lookup_kwargs(pk))
        instance = await self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer)


class UpdateModelMixin(BaseMixin):
    action = "update"

    async def update(self, pk: Any, data: Any = Body(...)) -> Response:
        """更新对象（全量或部分更新）"""
        self.kwargs.update(self._get_lookup_kwargs(pk))
        obj = await self.get_object()
        await obj.update_from_dict(self.serialize_input_data(data)).save()
        serializer = self.get_serializer(obj)
        return Response(serializer)


class PartialUpdateModelMixin(UpdateModelMixin):
    action = "partial_update"

    # 复用 UpdateModelMixin 的 update 方法即可
    async def partial_update(self, pk: Any, data: Any = Body(...)) -> Response:
        """部分更新对象"""
        return await self.update(pk, data)


class DestroyModelMixin(BaseMixin):
    action = "destroy"

    async def destroy(self, pk: Any) -> Response:
        """软删除对象"""
        self.kwargs.update(self._get_lookup_kwargs(pk))
        instance = await self.get_object()
        await self.perform_destroy(instance)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def perform_destroy(self, instance) -> None:
        """执行软删除操作"""
        await instance.update_from_dict({"is_deleted": True}).save()
