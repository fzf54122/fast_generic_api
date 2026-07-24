import pytest
from fastapi import APIRouter

from tests.conftest import build_client, make_item_viewset
from tests.models import ItemRecord


@pytest.mark.asyncio
async def test_search_across_fields(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/search-items",
        pagination_class=None,
        search_fields=["name", "description"],
    )
    await ItemRecord.create(name="Alpha", description="red apple")
    await ItemRecord.create(name="Beta", description="blue sky")
    await ItemRecord.create(name="Gamma", description="apple pie")

    async with await build_client(viewset) as client:
        response = await client.get("/search-items/?search=apple")
        assert response.status_code == 200
        names = {row["name"] for row in response.json()["data"]}
        assert names == {"Alpha", "Gamma"}


@pytest.mark.asyncio
async def test_force_pagination_when_no_pagination_class(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/force-page-items",
        pagination_class=None,
        force_pagination=True,
    )
    for index in range(3):
        await ItemRecord.create(name=f"Item{index}")

    async with await build_client(viewset) as client:
        response = await client.get("/force-page-items/?limit=2&offset=0")
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["total"] == 3
        assert payload["limit"] == 2
        assert len(payload["results"]) == 2
