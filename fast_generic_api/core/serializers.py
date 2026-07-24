# -*- coding: utf-8 -*-
# @FileName: serializers.py
# @Software: PyCharm
"""Tortoise ModelSerializer 支持。"""
from typing import Any, Optional

from pydantic._internal._model_construction import ModelMetaclass

from fast_generic_api.core.schemas import AutoSchemas


class ModelSerializerMeta(ModelMetaclass):
    """在 Pydantic 建模前，从 Tortoise model 注入字段注解。"""

    def __new__(mcls, name, bases, namespace, **kwargs):
        meta = namespace.get("Meta")
        model = getattr(meta, "model", None) if meta is not None else None
        if model is not None:
            annotations = dict(namespace.get("__annotations__", {}))
            field_names = _select_field_names(model, meta)
            read_only_fields = set(getattr(meta, "read_only_fields", ()) or ())
            fields_map = getattr(getattr(model, "_meta", None), "fields_map", {})

            for field_name in field_names:
                if field_name in annotations:
                    continue
                field = fields_map[field_name]
                field_type = _field_python_type(field)
                if _is_optional_field(field_name, field, read_only_fields):
                    field_type = Optional[field_type]
                    namespace.setdefault(field_name, None)
                elif _has_default(field):
                    namespace.setdefault(field_name, field.default)
                annotations[field_name] = field_type
            namespace["__annotations__"] = annotations
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _select_field_names(model: Any, meta: Any) -> list[str]:
    fields_map = getattr(getattr(model, "_meta", None), "fields_map", {})
    requested_fields = getattr(meta, "fields", None)
    excluded_fields = set(getattr(meta, "exclude", ()) or ())

    if requested_fields in (None, "__all__"):
        field_names = list(fields_map.keys())
    else:
        field_names = list(requested_fields)
        unknown_fields = set(field_names) - set(fields_map.keys())
        if unknown_fields:
            unknown = ", ".join(sorted(unknown_fields))
            raise ValueError(f"Unknown Meta.fields for {model.__name__}: {unknown}")

    return [field_name for field_name in field_names if field_name not in excluded_fields]


def _field_python_type(field: Any) -> type[Any]:
    field_type = getattr(field, "field_type", None)
    if field_type is not None:
        return field_type
    return Any


def _is_optional_field(field_name: str, field: Any, read_only_fields: set[str]) -> bool:
    return (
        field_name in read_only_fields
        or bool(getattr(field, "null", False))
        or bool(getattr(field, "pk", False))
    )


def _has_default(field: Any) -> bool:
    return getattr(field, "default", None) is not None


class ModelSerializer(AutoSchemas, metaclass=ModelSerializerMeta):
    """从 Tortoise Model 自动生成 Pydantic 字段的序列化器。

    用法：
        class ItemSerializer(ModelSerializer):
            class Meta:
                model = Item
                fields = ("id", "name")
                read_only_fields = ("id",)
    """

    def _writable_data(self) -> dict[str, Any]:
        read_only_fields = set(getattr(self.Meta, "read_only_fields", ()) or ())
        return self.model_dump(exclude_unset=True, exclude=read_only_fields)

    async def create(self):
        model = self.Meta.model
        return await model.create(**self._writable_data())

    async def update(self, instance):
        await instance.update_from_dict(self._writable_data()).save()
        return instance
