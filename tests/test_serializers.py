import pytest
from pydantic import ValidationError

from fast_generic_api.core.schemas import AutoSchemas
from fast_generic_api.core.serializers import ModelSerializer
from tests.models import ItemRecord


class ItemOut(AutoSchemas):
    id: int
    name: str
    description: str | None = None
    is_active: bool
    is_deleted: bool

    class Meta:
        fields = ("id", "name")


class ItemOutExclude(AutoSchemas):
    id: int
    name: str
    description: str | None = None
    is_deleted: bool

    class Meta:
        exclude = ("is_deleted", "description")


class ItemModelSerializer(ModelSerializer):
    class Meta:
        model = ItemRecord
        fields = ("id", "name", "description", "is_active", "is_deleted")
        read_only_fields = ("id", "is_deleted")


class ItemModelAllSerializer(ModelSerializer):
    class Meta:
        model = ItemRecord
        fields = "__all__"
        exclude = ("created_at",)
        read_only_fields = ("id", "created_at", "is_deleted")


def test_autoschemas_meta_fields_whitelist():
    payload = ItemOut.model_validate(
        {"id": 1, "name": "A", "description": "d", "is_active": True, "is_deleted": False}
    )
    assert payload.data == {"id": 1, "name": "A"}


def test_autoschemas_meta_exclude():
    payload = ItemOutExclude.model_validate(
        {"id": 1, "name": "A", "description": "d", "is_deleted": False}
    )
    assert payload.data == {"id": 1, "name": "A"}


def test_model_serializer_generates_fields_from_model():
    assert "name" in ItemModelSerializer.model_fields
    assert "description" in ItemModelSerializer.model_fields
    assert "id" in ItemModelSerializer.model_fields


def test_model_serializer_fields_all_with_exclude():
    assert "name" in ItemModelAllSerializer.model_fields
    assert "created_at" not in ItemModelAllSerializer.model_fields


def test_model_serializer_rejects_unknown_meta_fields():
    with pytest.raises(ValueError, match="Unknown Meta.fields"):
        class BrokenModelSerializer(ModelSerializer):
            class Meta:
                model = ItemRecord
                fields = ("id", "missing_field")


@pytest.mark.asyncio
async def test_model_serializer_create_and_update(db):
    created = await ItemModelSerializer(name="Alpha", description="first").create()
    assert created.id is not None
    assert created.name == "Alpha"

    ser = ItemModelSerializer(name="Beta", description="updated")
    updated = await ser.update(created)
    assert updated.name == "Beta"
    assert updated.description == "updated"

    # read_only id should not be required on input model for create helper path
    with pytest.raises(ValidationError):
        ItemModelSerializer()
