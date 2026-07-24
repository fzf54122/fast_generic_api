# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:41
# @Author  : fzf
# @FileName: main.py
# @Software: PyCharm
# main.py
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from tortoise.contrib.fastapi import register_tortoise

from fast_generic_api.core.exceptions import register_exception_handlers
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action
from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin
from model import Item
from serializers import (
    ItemCreateSerializer,
    ItemListSerializer,
    ItemSerializer,
    ItemSummarySerializer,
    ItemToggleSerializer,
    ItemUpdateSerializer,
)

app = FastAPI(
    title="Fast Generic API",
    description="FastAPI + Tortoise ORM 的自动化 CRUD 框架示例",
    version="0.1.0",
)

router = APIRouter(tags=["API示例"])


class ItemFilter(FilterSet):
    model = Item
    name__icontains: str | None = None
    description__contains: str | None = None

    filters = {
        "name": lambda qs, field, value: qs.filter(name__icontains=value),
    }


class ItemViewSet(CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet):
    router = router
    prefix = "/api/items"
    queryset = Item
    filter_class = ItemFilter
    ordering = ["-created_at"]
    ordering_fields = ["id", "name", "created_at"]
    batch_max_size = 100
    lookup_field = "id"

    serializer_class = ItemSerializer
    serializer_list_class = ItemListSerializer
    serializer_retrieve_class = ItemSerializer
    serializer_create_class = ItemCreateSerializer
    serializer_update_class = ItemUpdateSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=True, methods=["GET"], response_model=ItemSummarySerializer)
    async def summary(self, request: Request) -> Response:
        item = await self.get_object()
        description = item.description or ""
        return Response(
            ItemSummarySerializer(
                id=item.id,
                name=item.name,
                description_length=len(description),
            )
        )

    @action(detail=True, methods=["POST"], response_model=ItemToggleSerializer)
    async def toggle_deleted(self, request: Request) -> Response:
        item = await self.get_object()
        item.is_deleted = not item.is_deleted
        await self.backend.save(item)
        return Response(ItemToggleSerializer.model_validate(item))


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
