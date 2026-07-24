from tortoise import fields, models


class ItemRecord(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    is_deleted = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "test_items"


class HardItem(models.Model):
    """无 is_deleted：用于验证 destroy 物理删除回退。"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)

    class Meta:
        table = "hard_items"
