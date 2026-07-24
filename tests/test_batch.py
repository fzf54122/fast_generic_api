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
    toggle_active,
)
from tests.models import ItemRecord


def make_batch_viewset(api_router: APIRouter, *, prefix: str = "/batch-items", **overrides):
    attrs = {
        "router": api_router,
        "prefix": prefix,
        "queryset": ItemRecord,
        "lookup_field": "id",
        "filter_class": ItemFilter,
        "ordering": ["id"],
        "pagination_class": None,
        "serializer_class": ItemSerializer,
        "serializer_create_class": ItemCreateSerializer,
        "serializer_update_class": ItemUpdateSerializer,
        "serializer_list_class": ItemListSerializer,
        "toggle_active": toggle_active,
    }
    attrs.update(overrides)
    return type(
        f"{prefix.strip('/').replace('-', '_').title()}BatchViewSet",
        (CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet),
        attrs,
    )


@pytest.mark.asyncio
async def test_create_many_update_many_destroy_many_flow(db):
    viewset = make_batch_viewset(APIRouter())
    async with await build_client(viewset) as client:
        create_response = await client.post(
            "/batch-items/batch/",
            json={
                "items": [
                    {"name": "One", "description": "1"},
                    {"name": "Two", "description": "2"},
                ]
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()["data"]
        assert len(created) == 2
        assert {item["name"] for item in created} == {"One", "Two"}
        ids = [item["id"] for item in created]

        update_response = await client.put(
            "/batch-items/batch/",
            json={
                "items": [
                    {"id": ids[0], "name": "OneUpdated"},
                    {"id": ids[1], "description": "2-updated"},
                ]
            },
        )
        assert update_response.status_code == 200
        updated = {row["id"]: row for row in update_response.json()["data"]}
        assert updated[ids[0]]["name"] == "OneUpdated"
        assert updated[ids[1]]["description"] == "2-updated"

        delete_response = await client.request(
            "DELETE",
            "/batch-items/batch/",
            json={"ids": ids},
        )
        assert delete_response.status_code == 204

        assert await ItemRecord.filter(is_deleted=False).count() == 0
        assert await ItemRecord.filter(id__in=ids, is_deleted=True).count() == 2


@pytest.mark.asyncio
async def test_destroy_many_supports_query_ids(db):
    items = [
        await ItemRecord.create(name="A"),
        await ItemRecord.create(name="B"),
        await ItemRecord.create(name="C"),
    ]
    viewset = make_batch_viewset(APIRouter())
    async with await build_client(viewset) as client:
        ids = f"{items[0].id},{items[1].id}"
        response = await client.delete(f"/batch-items/batch/?ids={ids}")
        assert response.status_code == 204

        assert (await ItemRecord.get(id=items[0].id)).is_deleted is True
        assert (await ItemRecord.get(id=items[1].id)).is_deleted is True
        assert (await ItemRecord.get(id=items[2].id)).is_deleted is False


@pytest.mark.asyncio
async def test_update_many_removes_lookup_url_kwarg_from_payload(db):
    item = await ItemRecord.create(name="Alpha")
    viewset = make_batch_viewset(
        APIRouter(),
        prefix="/slug-batch-items",
        lookup_field="id",
        lookup_url_kwarg="item_id",
    )
    async with await build_client(viewset) as client:
        response = await client.put(
            "/slug-batch-items/batch/",
            json={"items": [{"item_id": item.id, "name": "Updated"}]},
        )
        assert response.status_code == 200
        await item.refresh_from_db()
        assert item.name == "Updated"


@pytest.mark.asyncio
async def test_create_many_rolls_back_on_failure(db):
    class FailingCreateMany(CreateManyMixin):
        async def perform_create(self, data):
            payload = self.serialize_input_data(data)
            if payload.get("name") == "fail":
                raise RuntimeError("boom")
            return await super().perform_create(data)

    attrs = {
        "router": APIRouter(),
        "prefix": "/batch-fail",
        "queryset": ItemRecord,
        "lookup_field": "id",
        "serializer_class": ItemSerializer,
        "serializer_create_class": ItemCreateSerializer,
        "serializer_update_class": ItemUpdateSerializer,
    }
    viewset = type(
        "FailingBatchViewSet",
        (FailingCreateMany, CustomViewSet),
        attrs,
    )

    async with await build_client(viewset) as client:
        with pytest.raises(RuntimeError):
            await client.post(
                "/batch-fail/batch/",
                json={
                    "items": [
                        {"name": "ok"},
                        {"name": "fail"},
                    ]
                },
            )
        assert await ItemRecord.filter(is_deleted=False).count() == 0
