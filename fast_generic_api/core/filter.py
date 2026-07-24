# -*- coding: utf-8 -*-
# @FileName: filter.py
# @Software: PyCharm
"""
声明式 FilterSet。

两种用法（按复杂程度递增）：

1. 声明式（推荐）：
    class ItemFilter(FilterSet):
        name: str | None = None            # 精确匹配
        name__icontains: str | None = None  # 模糊匹配，后缀约定同 Tortoise/SQLAlchemy backend

2. 自定义回调（兼容旧用法）：
    class ItemFilter(FilterSet):
        filters = { "name": lambda qs, val: qs.filter(name__icontains=val) }

声明式模式下会自动生成 Pydantic model，在 /docs 能看到所有查询参数。
"""
import inspect
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel, create_model


# 已知的双下划线查询后缀（不含 __）
LOOKUP_SUFFIXES = {
    "exact", "iexact", "contains", "icontains", "in", "gt", "gte", "lt", "lte",
    "startswith", "istartswith", "endswith", "iendswith",
    "range", "isnull", "not", "regex", "iregex",
}


class FilterSet:
    """
    声明式 FilterSet。

    子类通过类型注解声明可过滤字段及其类型（Pydantic 风格），
    框架通过 backend.filter 应用 ``__`` 后缀查询操作符。

    示例：
        class ItemFilter(FilterSet):
            name__icontains: str | None = None
            is_deleted: bool | None = None

    在 ViewSet 中：
        filter_class = ItemFilter
    """

    model = None
    # 自定义回调（兼容旧用法）：{field_name: callable(qs, value) -> qs}
    filters: Dict[str, Callable] = {}
    # 自动排除的字段（通常是分页参数）
    exclude_fields: set = {"offset", "limit", "page", "page_size"}

    def __init__(self, request=None, queryset=None, data: dict = None, backend=None):
        if self.model is None and queryset is None:
            raise ValueError("model or queryset must be defined")
        self.request = request
        self.backend = backend
        if queryset is not None:
            self.queryset = queryset
        elif backend is not None and self.model is not None:
            self.queryset = backend.get_queryset(self.model)
        elif self.model is not None and hasattr(self.model, "all"):
            # Tortoise 兼容：无 backend 时回退 model.all()
            self.queryset = self.model.all()
        else:
            raise ValueError("queryset or backend+model is required")

        if data is not None:
            raw_data = data
        elif request is not None:
            raw_data = dict(request.query_params)
        else:
            raw_data = {}

        request_model = self.get_request_model()
        if request_model is None:
            self.data = raw_data
        else:
            validated_data = request_model.model_validate(raw_data).model_dump(exclude_none=True)
            # 保留旧版 filters dict 中声明的查询参数，避免声明式迁移破坏旧用法
            for field_name in self.filters:
                if field_name in raw_data:
                    validated_data[field_name] = raw_data[field_name]
            self.data = validated_data

    def _apply_filter(self, qs, field: str, value: Any):
        """根据字段和值应用过滤"""
        if value is None or value == "":
            return qs
        # 自定义回调优先：兼容 callable(qs, value) 与旧版 callable(qs, field, value)
        if field in self.filters:
            callback = self.filters[field]
            parameter_count = len(inspect.signature(callback).parameters)
            if parameter_count >= 3:
                return callback(qs, field, value)
            return callback(qs, value)
        # 逗号分隔转 __in
        filter_kwargs = {f"{field}__in": value.split(",")} if isinstance(value, str) and "," in value else {field: value}
        if self.backend is not None:
            return self.backend.filter(qs, **filter_kwargs)
        # 兼容旧 Tortoise QuerySet
        return qs.filter(**filter_kwargs)

    def qs(self):
        """返回过滤后的 QuerySet / backend 查询对象"""
        qs = self.queryset
        for field, value in self.data.items():
            if field in self.exclude_fields:
                continue
            qs = self._apply_filter(qs, field, value)
        return qs

    @classmethod
    def get_request_model(cls) -> Optional[Type[BaseModel]]:
        """
        从子类的类型注解自动生成 FastAPI 可用的 request model。
        用于 ``Depends()`` 注入，自动生成 OpenAPI 查询参数。
        """
        if cls is FilterSet:
            return None

        field_definitions = {}
        for field_name, field_type in cls.__annotations__.items():
            if field_name.startswith("_"):
                continue
            if field_name in ("exclude_fields", "filters", "model"):
                continue
            field_definitions[field_name] = (field_type, None)

        if not field_definitions:
            return None

        model_name = f"{cls.__name__}Request"
        return create_model(model_name, **field_definitions)
