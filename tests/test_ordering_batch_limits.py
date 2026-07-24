import pytest
from fastapi import APIRouter

from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin
from tests.conftest import (
    ItemCreateSerializer,
    ItemFilter,
    ItemListSerializer,
    ItemSerializer,
    ItemUpdateSerializer,
    build_client,
    make_item_viewset,
    toggle_active,
)
from tests.models import ItemRecord


@pytest.mark.asyncio
async def test_ordering_query_param_whitelist(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/ordered-items",
        pagination_class=None,
        ordering=["id"],
        ordering_fields=["id", "name"],
    )
    await ItemRecord.create(name="Beta")
    await ItemRecord.create(name="Alpha")

    async with await build_client(viewset) as client:
        ok = await client.get("/ordered-items/?ordering=-name")
        assert ok.status_code == 200
        names = [row["name"] for row in ok.json()["data"]]
        assert names == ["Beta", "Alpha"]

        bad = await client.get("/ordered-items/?ordering=description")
        assert bad.status_code == 400
        assert bad.json()["code"] == 40000
        assert "description" in bad.json()["msg"]


@pytest.mark.asyncio
async def test_batch_max_size_enforced(db):
    router = APIRouter()
    viewset = type(
        "TinyBatchViewSet",
        (CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet),
        {
            "router": router,
            "prefix": "/tiny-batch",
            "queryset": ItemRecord,
            "lookup_field": "id",
            "filter_class": ItemFilter,
            "ordering": ["id"],
            "ordering_fields": ["id", "name"],
            "pagination_class": None,
            "serializer_class": ItemSerializer,
            "serializer_create_class": ItemCreateSerializer,
            "serializer_update_class": ItemUpdateSerializer,
            "serializer_list_class": ItemListSerializer,
            "toggle_active": toggle_active,
            "batch_max_size": 2,
        },
    )

    async with await build_client(viewset) as client:
        response = await client.post(
            "/tiny-batch/batch/",
            json={
                "items": [
                    {"name": "a"},
                    {"name": "b"},
                    {"name": "c"},
                ]
            },
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == 40000
        assert "batch_max_size=2" in body["msg"]
        assert await ItemRecord.filter(is_deleted=False).count() == 0
