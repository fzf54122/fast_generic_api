# -*- coding: utf-8 -*-
# @FileName: __init__.py
# @Software: PyCharm
from fast_generic_api.backends.base import BaseBackend
from fast_generic_api.backends.tortoise_orm import TortoiseBackend, tortoise_backend

try:
    from fast_generic_api.backends.sqlalchemy_orm import SQLAlchemyBackend
except ImportError:  # pragma: no cover - optional dependency
    SQLAlchemyBackend = None  # type: ignore

__all__ = [
    "BaseBackend",
    "TortoiseBackend",
    "tortoise_backend",
    "SQLAlchemyBackend",
]
