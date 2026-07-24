# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:49
# @Author  : fzf
# @FileName: serializers.py
# @Software: PyCharm
# serializers.py
from typing import Optional

from fast_generic_api.core.schemas import AutoSchemas


class ItemSerializer(AutoSchemas):
    id: int
    name: str
    description: Optional[str] = None
    is_deleted: bool


class ItemListSerializer(AutoSchemas):
    id: int
    name: str


class ItemCreateSerializer(AutoSchemas):
    name: str
    description: Optional[str] = None


class ItemUpdateSerializer(AutoSchemas):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemSummarySerializer(AutoSchemas):
    id: int
    name: str
    description_length: int


class ItemToggleSerializer(AutoSchemas):
    id: int
    is_deleted: bool
