# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:49
# @Author  : fzf
# @FileName: mixins.py
# @Software: PyCharm
from typing import Any, Awaitable, Callable, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field

from fast_generic_api.core import status
from fast_generic_api.core.exceptions import HTTPException
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action as api_action

R = TypeVar("R")


class BatchCreatePayload(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class BatchUpdatePayload(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class BatchDestroyPayload(BaseModel):
    ids: list[Any] = Field(default_factory=list)


class BaseMixin:
    """提供通用工具方法"""

    def _get_lookup_kwargs(self, pk: Any) -> dict:
        lookup_field = self.lookup_url_kwarg or self.lookup_field
        return {lookup_field: pk}

    def _validate_input(self, serializer_class, data: Any):
        if serializer_class is None or not hasattr(serializer_class, "model_validate"):
            return data
        return serializer_class.model_validate(data)

    async def _get_object_by_lookup(self, lookup_value: Any):
        queryset = self.filter_queryset(self.get_queryset())
        obj = await self.backend.first(
            self.backend.filter(queryset, **{self.lookup_field: lookup_value})
        )
        if not obj:
            raise HTTPException
        await self.check_object_permissions(obj)
        return obj

    async def _run_atomic(self, fn: Callable[[], Awaitable[R]]) -> R:
        """写操作事务样板：atomic_actions=True 时包裹 backend.in_transaction()。"""
        if getattr(self, "atomic_actions", True):
            async with self.backend.in_transaction():
                return await fn()
        return await fn()

    def _model_has_field(self, field_name: str) -> bool:
        queryset = self.get_queryset()
        model = self.backend.resolve_model(queryset)
        meta = self.backend.get_model_meta(model)
        fields_map = getattr(meta, "fields_map", {}) if meta is not None else {}
        return field_name in fields_map


class CreateModelMixin(BaseMixin):
    action = "create"

    async def create(self, request: Request, data: Any) -> Response:
        """通用创建方法，默认开启事务"""
        await self.check_permissions()

        async def _do():
            obj = await self.perform_create(data)
            serializer = self.get_serializer(obj)
            return Response(serializer, status_code=status.HTTP_201_CREATED)

        return await self._run_atomic(_do)

    async def perform_create(self, data) -> Any:
        """执行创建，子类可覆盖以实现多表写入"""
        data_dict = self.serialize_input_data(data)
        queryset = self.get_queryset()
        model = self.backend.resolve_model(queryset)
        return await self.backend.create(model, **data_dict)


class CreateManyMixin(CreateModelMixin):
    action = "create_many"

    @api_action(detail=False, methods=["POST"], url_path="batch")
    async def create_many(self, request: Request, data: BatchCreatePayload) -> Response:
        """批量创建；任意一条失败时整体回滚。"""
        await self.check_permissions()
        input_serializer = self.serializer_create_class or self.serializer_class

        async def _do():
            objects = []
            for item in data.items:
                validated = self._validate_input(input_serializer, item)
                objects.append(await self.perform_create(validated))
            return Response(
                self.get_serializer(objects, many=True),
                status_code=status.HTTP_201_CREATED,
            )

        return await self._run_atomic(_do)


class ListModelMixin(BaseMixin):
    action = "list"
    ordering: list = []

    async def list(self, request: Request) -> Response:
        """获取对象列表，支持过滤、排序和分页"""
        await self.check_permissions()
        qs = self.filter_queryset(self.get_queryset())
        if self.ordering:
            qs = self.backend.order_by(qs, *self.ordering)

        if self.pagination_class is not None:
            result = await self.pagination_class.get_paginated_response(
                request, qs, self.get_serializer, backend=self.backend
            )
            return Response(result)

        serializer = self.get_serializer(await self.backend.all(qs), many=True)
        return Response(serializer)


class RetrieveModelMixin(BaseMixin):
    action = "retrieve"

    async def retrieve(self, request: Request) -> Response:
        """获取单个对象，路径参数已写入 self.kwargs"""
        instance = await self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer)


class UpdateModelMixin(BaseMixin):
    action = "update"

    async def update(self, request: Request, data: Any) -> Response:
        """全量更新对象，默认开启事务；路径参数已写入 self.kwargs"""

        async def _do():
            obj = await self.get_object()
            await self.perform_update(obj, data)
            serializer = self.get_serializer(obj)
            return Response(serializer)

        return await self._run_atomic(_do)

    async def perform_update(self, instance, data) -> None:
        """执行更新，子类可覆盖"""
        await self.backend.update_from_dict(instance, self.serialize_input_data(data))


class UpdateManyMixin(UpdateModelMixin):
    action = "update_many"

    @api_action(detail=False, methods=["PUT"], url_path="batch")
    async def update_many(self, request: Request, data: BatchUpdatePayload) -> Response:
        """批量更新；body.items 每项必须包含 lookup_field。"""
        await self.check_permissions()
        input_serializer = self.serializer_update_class or self.serializer_class

        async def _do():
            objects = []
            for item in data.items:
                lookup_value = item.get(self.lookup_field)
                if lookup_value is None:
                    lookup_value = item.get(self.lookup_url_kwarg or self.lookup_field)
                if lookup_value is None:
                    raise HTTPException
                obj = await self._get_object_by_lookup(lookup_value)
                lookup_keys = {self.lookup_field, self.lookup_url_kwarg or self.lookup_field}
                update_data = {key: value for key, value in item.items() if key not in lookup_keys}
                validated = self._validate_input(input_serializer, update_data)
                await self.perform_update(obj, validated)
                objects.append(obj)
            return Response(self.get_serializer(objects, many=True))

        return await self._run_atomic(_do)


class PartialUpdateModelMixin(UpdateModelMixin):
    action = "partial_update"

    async def partial_update(self, request: Request, data: Any) -> Response:
        """部分更新对象，复用 update 逻辑（data 已是 exclude_unset）"""
        return await self.update(request, data)


class DestroyModelMixin(BaseMixin):
    action = "destroy"

    async def destroy(self, request: Request) -> Response:
        """删除对象，默认开启事务；有 is_deleted 则软删，否则物理删除。"""

        async def _do():
            instance = await self.get_object()
            await self.perform_destroy(instance)

        await self._run_atomic(_do)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def perform_destroy(self, instance) -> None:
        """优先软删除；模型无 is_deleted 字段时回退物理删除。"""
        if self._model_has_field("is_deleted"):
            await self.backend.update_from_dict(instance, {"is_deleted": True})
            return
        await self.backend.delete(instance)


class DestroyManyMixin(DestroyModelMixin):
    action = "destroy_many"

    @api_action(detail=False, methods=["DELETE"], url_path="batch")
    async def destroy_many(
        self,
        request: Request,
        data: BatchDestroyPayload | None = None,
    ) -> Response:
        """批量删除；支持 body.ids 或 query 参数 ?ids=1,2,3。"""
        await self.check_permissions()
        ids = self._get_destroy_ids(request, data)

        async def _do():
            for lookup_value in ids:
                obj = await self._get_object_by_lookup(lookup_value)
                await self.perform_destroy(obj)

        await self._run_atomic(_do)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    def _get_destroy_ids(self, request: Request, data: BatchDestroyPayload | None) -> list[Any]:
        if data is not None and data.ids:
            return data.ids
        raw_ids = request.query_params.get("ids", "")
        if not raw_ids:
            return []
        return [item for item in raw_ids.split(",") if item]
