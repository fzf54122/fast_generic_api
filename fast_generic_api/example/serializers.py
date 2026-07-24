# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:49
# @Author  : fzf
# @FileName: serializers.py
# @Software: PyCharm
from typing import List, Optional

from pydantic import BaseModel, Field

from fast_generic_api.core.schemas import AutoSchemas


class ItemSerializer(AutoSchemas):
    id: int
    name: str
    description: Optional[str] = None
    institution_id: Optional[str] = None
    is_deleted: bool


class ItemListSerializer(AutoSchemas):
    id: int
    name: str
    institution_id: Optional[str] = None


class ItemCreateSerializer(AutoSchemas):
    name: str
    description: Optional[str] = None
    institution_id: Optional[str] = None
    # 可选：创建时顺带写入子 notes
    notes: List[str] = Field(default_factory=list)


class ItemUpdateSerializer(AutoSchemas):
    name: Optional[str] = None
    description: Optional[str] = None
    institution_id: Optional[str] = None


class ItemSummarySerializer(AutoSchemas):
    id: int
    name: str
    description_length: int
    note_count: int = 0


class ItemToggleSerializer(AutoSchemas):
    id: int
    is_deleted: bool


class NoteSerializer(AutoSchemas):
    id: int
    content: str
    institution_id: Optional[str] = None
    is_deleted: bool
    item_id: int


class NoteCreateSerializer(BaseModel):
    content: str
    item_id: int
    institution_id: Optional[str] = None


class NoteUpdateSerializer(BaseModel):
    content: Optional[str] = None
