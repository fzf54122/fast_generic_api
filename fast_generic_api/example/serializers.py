# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:49
# @Author  : fzf
# @FileName: serializers.py
# @Software: PyCharm
# serializers.py
from pydantic import BaseModel
from typing import Optional
from fast_generic_api.core.serializers import CoreSerializer


class ItemSerializer(CoreSerializer):
    id: int
    name: str
    description: Optional[str] = None
    is_deleted: bool


class ItemCreateSerializer(CoreSerializer):
    name: str
    description: Optional[str] = None


class ItemUpdateSerializer(CoreSerializer):
    name: Optional[str] = None
    description: Optional[str] = None
