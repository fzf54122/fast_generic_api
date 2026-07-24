# -*- coding: utf-8 -*-
# @FileName: base.py
# @Software: PyCharm
"""
Backend 抽象层。

把所有 ORM 直接调用收口到 Backend，ViewSet/Mixin 只依赖抽象接口。
这样未来要支持 SQLAlchemy 或其他异步 ORM 时，只需新增一个 Backend 实现，
而不必改动 generics / mixins 里的业务逻辑。

抽象方法以 Tortoise 的语义为基准（因为它是第一个实现），
但接口设计尽量保持 ORM 无关。
"""
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Iterable


class BaseBackend(ABC):
    """ORM 适配抽象基类。"""

    # ------------------------------------------------------------------
    # 查询集构建
    # ------------------------------------------------------------------
    @abstractmethod
    def get_queryset(self, model: Any):
        """返回该 model 的初始查询集（等价 Model.all()）"""

    @abstractmethod
    def filter(self, queryset, **kwargs):
        """对查询集应用过滤条件"""

    @abstractmethod
    def order_by(self, queryset, *fields: str):
        """对查询集排序"""

    @abstractmethod
    def select_related(self, queryset, *fields: str):
        """关联查询（join，解决外键 N+1）"""

    @abstractmethod
    def prefetch_related(self, queryset, *fields: str):
        """预取关联（额外查询，解决多对多/反向 N+1）"""

    @abstractmethod
    def offset_limit(self, queryset, offset: int, limit: int):
        """分页切片"""

    def search(self, queryset, fields: list[str], term: str):
        """跨字段模糊搜索（OR）。默认未实现时原样返回。"""
        return queryset

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------
    @abstractmethod
    async def count(self, queryset) -> int:
        """返回查询集总数"""

    @abstractmethod
    async def first(self, queryset):
        """返回第一条，无则 None"""

    @abstractmethod
    async def all(self, queryset) -> list:
        """执行查询，返回实例列表"""

    # ------------------------------------------------------------------
    # 写操作
    # ------------------------------------------------------------------
    @abstractmethod
    async def create(self, model: Any, **kwargs):
        """创建并保存一条记录"""

    @abstractmethod
    async def save(self, instance) -> None:
        """保存实例修改"""

    @abstractmethod
    async def update_from_dict(self, instance, data: dict) -> None:
        """用 dict 更新实例字段并保存"""

    @abstractmethod
    async def delete(self, instance) -> None:
        """物理删除实例"""

    # ------------------------------------------------------------------
    # 元信息
    # ------------------------------------------------------------------
    @abstractmethod
    def resolve_model(self, queryset_or_model: Any) -> Any:
        """从 queryset 或 model 中解析出 Model 类"""

    @abstractmethod
    def get_model_meta(self, model: Any):
        """返回模型元信息对象，含 fields_map（用于判断 is_deleted 等字段是否存在）"""

    # ------------------------------------------------------------------
    # 事务
    # ------------------------------------------------------------------
    @abstractmethod
    @asynccontextmanager
    async def in_transaction(self):
        """事务上下文管理器"""
