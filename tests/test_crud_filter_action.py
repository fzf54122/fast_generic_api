import pytest

from tests.models import ItemRecord


@pytest.mark.asyncio
async def test_create_retrieve_update_partial_destroy_flow(client):
    create_response = await client.post(
        "/items/",
        json={"name": "Alpha", "description": "first item"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["code"] == 200
    assert created["data"]["name"] == "Alpha"

    item_id = created["data"]["id"]

    retrieve_response = await client.get(f"/items/{item_id}/")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["data"]["description"] == "first item"

    update_response = await client.put(
        f"/items/{item_id}/",
        json={"name": "Beta", "description": "updated", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Beta"
    assert update_response.json()["data"]["is_active"] is False

    partial_response = await client.patch(
        f"/items/{item_id}/",
        json={"description": "patched"},
    )
    assert partial_response.status_code == 200
    assert partial_response.json()["data"]["name"] == "Beta"
    assert partial_response.json()["data"]["description"] == "patched"

    delete_response = await client.delete(f"/items/{item_id}/")
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/items/{item_id}/")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == 40400

    item = await ItemRecord.get(id=item_id)
    assert item.is_deleted is True


@pytest.mark.asyncio
async def test_list_filters_and_limit_offset_pagination(client):
    await ItemRecord.create(name="Alpha", description="first", is_active=True)
    await ItemRecord.create(name="Beta", description="second", is_active=True)
    await ItemRecord.create(name="Gamma", description="third", is_active=False)

    response = await client.get("/items/?name__icontains=a&is_active=true&limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["total"] == 2
    assert payload["data"]["limit"] == 1
    assert payload["data"]["offset"] == 1
    assert payload["data"]["results"] == [{"id": 2, "name": "Beta"}]


@pytest.mark.asyncio
async def test_detail_action_can_mutate_object(client):
    item = await ItemRecord.create(name="Alpha", is_active=True)

    response = await client.post(f"/items/{item.id}/toggle-active/")

    assert response.status_code == 200
    assert response.json()["data"] == {"id": item.id, "is_active": False}
    await item.refresh_from_db()
    assert item.is_active is False
