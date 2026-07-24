# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午6:30
# @Author  : fzf
# @FileName: schemas.py
# @Software: PyCharm
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from tortoise.fields.relational import ManyToManyRelation


class AutoSchemas(BaseModel):
    """基础 BaseModel，提供 `.data` 属性返回 JSON 可序列化内容。"""

    model_config = {"from_attributes": True}

    @classmethod
    def _meta_fields(cls) -> set[str] | None:
        meta = getattr(cls, "Meta", None)
        fields = getattr(meta, "fields", None)
        if fields in (None, "__all__"):
            return None
        return set(fields)

    @classmethod
    def _meta_exclude(cls) -> set[str]:
        meta = getattr(cls, "Meta", None)
        return set(getattr(meta, "exclude", ()) or ())

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        if kwargs.get("include") is None:
            meta_fields = self._meta_fields()
            if meta_fields is not None:
                kwargs["include"] = meta_fields
        exclude = set(kwargs.pop("exclude", set()) or set())
        exclude.update(self._meta_exclude())
        if exclude:
            kwargs["exclude"] = exclude
        return super().model_dump(*args, **kwargs)

    @property
    def data(self) -> Any:
        """返回可直接用于 FastAPI JSONResponse 的 dict。"""
        return jsonable_encoder(self.model_dump())

    def model_post_init(self, __context: Any) -> None:
        obj = __context
        if obj is None or not hasattr(obj, "_meta"):
            return
        for field_name in getattr(obj, "_meta").fields_map.keys():
            value = getattr(obj, field_name, None)
            if isinstance(value, ManyToManyRelation):
                try:
                    value_list = list(value)
                except TypeError:
                    value_list = []
                setattr(obj, field_name, value_list)
