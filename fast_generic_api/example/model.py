# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午5:49
# @Author  : fzf
# @FileName: model.py
# @Software: PyCharm
from tortoise import fields, models


class Item(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    institution_id = fields.CharField(max_length=64, null=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "items"


class Note(models.Model):
    """Item 的子资源示例：演示 FK + 机构隔离 + 多表写入。"""

    id = fields.IntField(pk=True)
    item = fields.ForeignKeyField("models.Item", related_name="notes")
    content = fields.TextField()
    institution_id = fields.CharField(max_length=64, null=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "notes"
