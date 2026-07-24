import pytest

from tests.models import ItemRecord


@pytest.mark.asyncio
async def test_permission_classes_accept_classes_and_block_request(denied_client):
    response = await denied_client.get("/denied-items/")

    assert response.status_code == 403
    assert response.json()["code"] == 40300


@pytest.mark.asyncio
async def test_object_permission_runs_after_lookup(object_permission_client):
    active = await ItemRecord.create(name="Active", is_active=True)
    inactive = await ItemRecord.create(name="Inactive", is_active=False)

    allowed_response = await object_permission_client.get(f"/object-items/{active.id}/")
    denied_response = await object_permission_client.get(f"/object-items/{inactive.id}/")

    assert allowed_response.status_code == 200
    assert allowed_response.json()["data"]["id"] == active.id
    assert denied_response.status_code == 403
    assert denied_response.json()["code"] == 40300


@pytest.mark.asyncio
async def test_page_number_pagination(page_client):
    for index in range(5):
        await ItemRecord.create(name=f"Item {index}")

    response = await page_client.get("/page-items/?page=2&page_size=2")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 5
    assert payload["page"] == 2
    assert payload["page_size"] == 2
    assert payload["results"] == [
        {"id": 3, "name": "Item 2"},
        {"id": 4, "name": "Item 3"},
    ]
