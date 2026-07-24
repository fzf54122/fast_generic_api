# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:41
# @Author  : fzf
# @FileName: main.py
# @Software: PyCharm
"""
示例应用：Item + Note 双资源。

演示：
- CRUD / batch / filter / ordering / search / pagination
- 自定义 action
- 机构隔离（X-Institution-Id header）
- perform_create 多表事务写入 notes
"""
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from tortoise.contrib.fastapi import register_tortoise

from fast_generic_api import VERSION
from fast_generic_api.core.exceptions import register_exception_handlers
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action
from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin
from model import Item, Note
from serializers import (
    ItemCreateSerializer,
    ItemListSerializer,
    ItemSerializer,
    ItemSummarySerializer,
    ItemToggleSerializer,
    ItemUpdateSerializer,
    NoteCreateSerializer,
    NoteSerializer,
    NoteUpdateSerializer,
)

app = FastAPI(
    title="Fast Generic API",
    description="FastAPI + Tortoise ORM 的自动化 CRUD 框架示例",
    version=VERSION,
)

router = APIRouter(tags=["API示例"])


def institution_id_from_request(request: Request) -> str | None:
    return request.headers.get("X-Institution-Id")


class ItemFilter(FilterSet):
    model = Item
    name__icontains: str | None = None
    description__contains: str | None = None
    institution_id: str | None = None


class ItemViewSet(CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet):
    router = router
    prefix = "/api/items"
    queryset = Item
    filter_class = ItemFilter
    ordering = ["-created_at"]
    ordering_fields = ["id", "name", "created_at"]
    search_fields = ["name", "description"]
    batch_max_size = 100
    force_pagination = True
    lookup_field = "id"

    serializer_class = ItemSerializer
    serializer_list_class = ItemListSerializer
    serializer_retrieve_class = ItemSerializer
    serializer_create_class = ItemCreateSerializer
    serializer_update_class = ItemUpdateSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        qs = super().get_queryset()
        institution_id = institution_id_from_request(self.request) if self.request else None
        if institution_id:
            self.context["institution_id"] = institution_id
            qs = self.backend.filter(qs, institution_id=institution_id)
        return qs

    async def perform_create(self, data):
        """创建 Item，可选同事务写入 notes。"""
        payload = self.serialize_input_data(data)
        notes = payload.pop("notes", []) or []
        if self.context.get("institution_id") and not payload.get("institution_id"):
            payload["institution_id"] = self.context["institution_id"]
        item = await self.backend.create(Item, **payload)
        for content in notes:
            await self.backend.create(
                Note,
                item_id=item.id,
                content=content,
                institution_id=payload.get("institution_id"),
            )
        return item

    @action(detail=True, methods=["GET"], response_model=ItemSummarySerializer)
    async def summary(self, request: Request) -> Response:
        item = await self.get_object()
        description = item.description or ""
        note_count = await self.backend.count(
            self.backend.filter(self.backend.get_queryset(Note), item_id=item.id, is_deleted=False)
        )
        return Response(
            ItemSummarySerializer(
                id=item.id,
                name=item.name,
                description_length=len(description),
                note_count=note_count,
            )
        )

    @action(detail=True, methods=["POST"], response_model=ItemToggleSerializer)
    async def toggle_deleted(self, request: Request) -> Response:
        item = await self.get_object()
        item.is_deleted = not item.is_deleted
        await self.backend.save(item)
        return Response(ItemToggleSerializer.model_validate(item))


class NoteFilter(FilterSet):
    model = Note
    content__icontains: str | None = None
    item_id: int | None = None
    institution_id: str | None = None


class NoteViewSet(CustomViewSet):
    router = router
    prefix = "/api/notes"
    queryset = Note
    filter_class = NoteFilter
    ordering = ["-created_at"]
    ordering_fields = ["id", "created_at"]
    search_fields = ["content"]
    lookup_field = "id"
    serializer_class = NoteSerializer
    serializer_create_class = NoteCreateSerializer
    serializer_update_class = NoteUpdateSerializer
    pagination_class = LimitOffsetPagination
    force_pagination = True

    def get_queryset(self):
        qs = super().get_queryset()
        institution_id = institution_id_from_request(self.request) if self.request else None
        if institution_id:
            qs = self.backend.filter(qs, institution_id=institution_id)
        return qs


@app.get("/health")
async def health():
    return {"status": "ok", "version": VERSION}


app.include_router(router)
register_exception_handlers(app)

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["model"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
