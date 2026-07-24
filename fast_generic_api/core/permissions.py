# -*- coding: utf-8 -*-
# @FileName: permissions.py
# @Software: PyCharm
"""
权限基类与常用实现，语义对齐 DRF。

- ``permission_classes``：业务权限，作用于 list/create 前（has_permission）
  与 retrieve/update/destroy 取对象后（has_object_permission）
- ``permissions``（ViewSet 上）：FastAPI 依赖列表，通常用于认证（OAuth2 等）
"""
from typing import Any

from fastapi import Request


class BasePermission:
    """权限基类，子类覆写 has_permission / has_object_permission"""

    async def has_permission(self, request: Request) -> bool:
        return True

    async def has_object_permission(self, request: Request, obj: Any) -> bool:
        return True


class AllowAny(BasePermission):
    async def has_permission(self, request: Request) -> bool:
        return True


class IsAuthenticated(BasePermission):
    async def has_permission(self, request: Request) -> bool:
        user = getattr(request, "user", None)
        return user is not None


class IsAdminUser(BasePermission):
    async def has_permission(self, request: Request) -> bool:
        user = getattr(request, "user", None)
        if user is None:
            return False
        return bool(getattr(user, "is_staff", False) or getattr(user, "is_admin", False))
