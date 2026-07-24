# -*- coding: utf-8 -*-
# @FileName: sqlalchemy_orm.py
# @Software: PyCharm
"""SQLAlchemy 2.x async Backend 实现。"""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import Select, asc, desc, func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.elements import ColumnElement

from fast_generic_api.backends.base import BaseBackend


@dataclass
class _SQLAQuery:
    """轻量查询对象，模仿 Tortoise QuerySet 的链式接口语义。"""

    model: type
    session: AsyncSession
    statement: Select
    options: list = field(default_factory=list)

    def clone(self, **kwargs) -> "_SQLAQuery":
        data = {
            "model": self.model,
            "session": self.session,
            "statement": self.statement,
            "options": list(self.options),
        }
        data.update(kwargs)
        return _SQLAQuery(**data)

    def filter(self, **kwargs) -> "_SQLAQuery":
        """兼容自定义 FilterSet 回调里的 ``qs.filter(...)`` 写法。"""
        statement = self.statement
        for key, value in kwargs.items():
            statement = statement.where(_build_clause(self.model, key, value))
        return self.clone(statement=statement)

    def order_by(self, *fields: str) -> "_SQLAQuery":
        order_clauses = []
        for name in fields:
            if name.startswith("-"):
                order_clauses.append(desc(_get_column(self.model, name[1:])))
            else:
                order_clauses.append(asc(_get_column(self.model, name)))
        return self.clone(statement=self.statement.order_by(*order_clauses))


class _SQLAModelMeta:
    """兼容 generics 对 meta.fields_map 的访问。"""

    def __init__(self, fields_map: dict[str, Any]):
        self.fields_map = fields_map


class SQLAlchemyBackend(BaseBackend):
    """SQLAlchemy 2.x AsyncSession 适配器。

    用法：
        backend = SQLAlchemyBackend(session)
        viewset.backend = backend
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # 查询集构建
    # ------------------------------------------------------------------
    def get_queryset(self, model: Any) -> _SQLAQuery:
        return _SQLAQuery(model=model, session=self.session, statement=select(model))

    def filter(self, queryset: _SQLAQuery, **kwargs) -> _SQLAQuery:
        return queryset.filter(**kwargs)

    def order_by(self, queryset: _SQLAQuery, *fields: str) -> _SQLAQuery:
        return queryset.order_by(*fields)

    def select_related(self, queryset: _SQLAQuery, *fields: str) -> _SQLAQuery:
        options = list(queryset.options)
        for name in fields:
            options.append(joinedload(getattr(queryset.model, name)))
        return queryset.clone(options=options)

    def prefetch_related(self, queryset: _SQLAQuery, *fields: str) -> _SQLAQuery:
        options = list(queryset.options)
        for name in fields:
            options.append(selectinload(getattr(queryset.model, name)))
        return queryset.clone(options=options)

    def offset_limit(self, queryset: _SQLAQuery, offset: int, limit: int) -> _SQLAQuery:
        return queryset.clone(statement=queryset.statement.offset(offset).limit(limit))

    def search(self, queryset: _SQLAQuery, fields: list[str], term: str) -> _SQLAQuery:
        if not term or not fields:
            return queryset
        from sqlalchemy import or_

        clauses = []
        for field_name in fields:
            column = _get_column(queryset.model, field_name)
            clauses.append(column.ilike(f"%{term}%"))
        return queryset.clone(statement=queryset.statement.where(or_(*clauses)))

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------
    async def count(self, queryset: _SQLAQuery) -> int:
        count_stmt = select(func.count()).select_from(queryset.statement.order_by(None).subquery())
        result = await self.session.execute(count_stmt)
        return int(result.scalar_one())

    async def first(self, queryset: _SQLAQuery):
        statement = queryset.statement
        if queryset.options:
            statement = statement.options(*queryset.options)
        result = await self.session.execute(statement.limit(1))
        return result.scalars().first()

    async def all(self, queryset: _SQLAQuery) -> list:
        statement = queryset.statement
        if queryset.options:
            statement = statement.options(*queryset.options)
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    # ------------------------------------------------------------------
    # 写操作
    # ------------------------------------------------------------------
    async def create(self, model: Any, **kwargs):
        instance = model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def save(self, instance) -> None:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)

    async def update_from_dict(self, instance, data: dict) -> None:
        for key, value in data.items():
            setattr(instance, key, value)
        await self.save(instance)

    async def delete(self, instance) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    # ------------------------------------------------------------------
    # 元信息
    # ------------------------------------------------------------------
    def resolve_model(self, queryset_or_model: Any) -> Any:
        if isinstance(queryset_or_model, _SQLAQuery):
            return queryset_or_model.model
        return queryset_or_model

    def get_model_meta(self, model: Any):
        try:
            mapper = sa_inspect(model)
        except Exception:
            return None
        fields_map = {column.key: column for column in mapper.columns}
        # relationships also count as attributes for soft-delete checks we only need columns
        return _SQLAModelMeta(fields_map=fields_map)

    # ------------------------------------------------------------------
    # 事务
    # ------------------------------------------------------------------
    @asynccontextmanager
    async def in_transaction(self):
        # 已在事务中时直接复用；否则开启新事务
        if self.session.in_transaction():
            yield
            return
        async with self.session.begin():
            yield


def _get_column(model: type, name: str):
    column = getattr(model, name, None)
    if column is None:
        raise AttributeError(f"{model.__name__} has no column/attribute '{name}'")
    return column


def _build_clause(model: type, key: str, value: Any) -> ColumnElement:
    if "__" in key:
        field_name, lookup = key.rsplit("__", 1)
    else:
        field_name, lookup = key, "exact"

    column = _get_column(model, field_name)

    if lookup in ("exact", "eq"):
        return column == value
    if lookup == "iexact":
        return func.lower(column) == func.lower(value)
    if lookup == "contains":
        return column.contains(value)
    if lookup == "icontains":
        return column.ilike(f"%{value}%")
    if lookup == "in":
        values = value if not isinstance(value, str) else [item for item in value.split(",") if item]
        return column.in_(values)
    if lookup == "gt":
        return column > value
    if lookup == "gte":
        return column >= value
    if lookup == "lt":
        return column < value
    if lookup == "lte":
        return column <= value
    if lookup == "startswith":
        return column.startswith(value)
    if lookup == "istartswith":
        return column.ilike(f"{value}%")
    if lookup == "endswith":
        return column.endswith(value)
    if lookup == "iendswith":
        return column.ilike(f"%{value}")
    if lookup == "isnull":
        return column.is_(None) if value else column.is_not(None)
    if lookup == "range":
        low, high = value
        return column.between(low, high)
    if lookup == "not":
        return column != value
    raise ValueError(f"Unsupported SQLAlchemy lookup: {lookup}")
