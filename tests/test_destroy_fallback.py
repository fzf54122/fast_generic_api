import pytest
from fastapi import APIRouter
from pydantic import BaseModel

from fast_generic_api.generics import CustomViewSet
from tests.conftest import build_client
from tests.models import HardItem


class HardItemSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str


class HardItemCreateSerializer(BaseModel):
    name: str


@pytest.mark.asyncio
async def test_destroy_physically_deletes_when_no_soft_delete_field(db):
    viewset = type(
        "HardItemViewSet",
        (CustomViewSet,),
        {
            "router": APIRouter(),
            "prefix": "/hard-items",
            "queryset": HardItem,
            "lookup_field": "id",
            "serializer_class": HardItemSerializer,
            "serializer_create_class": HardItemCreateSerializer,
            "serializer_update_class": HardItemCreateSerializer,
            "pagination_class": None,
        },
    )

    async with await build_client(viewset) as client:
        created = await client.post("/hard-items/", json={"name": "tmp"})
        assert created.status_code == 201
        item_id = created.json()["data"]["id"]

        deleted = await client.delete(f"/hard-items/{item_id}/")
        assert deleted.status_code == 204

        missing = await client.get(f"/hard-items/{item_id}/")
        assert missing.status_code == 404
        assert await HardItem.filter(id=item_id).count() == 0
