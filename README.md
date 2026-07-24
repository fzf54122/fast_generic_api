# fast_generic_api

<div align="center">

**FastAPI 版 DRF 风格通用 CRUD 框架**  
Tortoise ORM（默认）· SQLAlchemy 2.x async（可选）· 统一响应信封 · 测试覆盖

**简体中文** | [English](README.en.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PyPI](https://img.shields.io/badge/PyPI-1.0.0-blue.svg)](https://pypi.org/project/fast-generic-api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 特性

| 能力 | 说明 |
|------|------|
| RESTful CRUD | list / create / retrieve / update / partial_update / destroy |
| 批量操作 | `CreateManyMixin` / `UpdateManyMixin` / `DestroyManyMixin` → `/batch/` |
| `@action` | 自定义 detail / collection 路由 |
| 声明式 FilterSet | Pydantic 风格查询参数，进 OpenAPI |
| 排序 / 搜索 | `?ordering=` 白名单，`?search=` + `search_fields` |
| 分页 | `LimitOffsetPagination` / `PageNumberPagination`，可 `force_pagination` |
| 权限 | `permission_classes` + FastAPI `permissions` 依赖 |
| 软删 / 硬删 | 有 `is_deleted` 软删，否则物理删除 |
| 多 ORM | `TortoiseBackend` 默认，`SQLAlchemyBackend` 可选 |
| 响应信封 | `{code,status,data,msg}`，OpenAPI `Envelope[T]` |
| 事务 | 写操作默认 `backend.in_transaction()` |
| 节流 | 可选 `throttle_classes`（进程内） |

当前版本：**1.0.0**（公开 API 冻结，破坏性变更走 major）

## 安装

```bash
pip install fast-generic-api==1.0.0

# 可选 SQLAlchemy
pip install "fast-generic-api[sqlalchemy]"
```

开发安装：

```bash
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_generic_api
pip install -e ".[test]"
pytest tests/ -q
```

## 快速开始

```python
from fastapi import APIRouter, FastAPI
from tortoise import fields, models
from tortoise.contrib.fastapi import register_tortoise

from fast_generic_api.core.exceptions import register_exception_handlers
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination
from fast_generic_api.core.schemas import AutoSchemas
from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin


class Item(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_deleted = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "items"


class ItemSerializer(AutoSchemas):
    id: int
    name: str
    description: str | None = None
    is_deleted: bool


class ItemCreateSerializer(AutoSchemas):
    name: str
    description: str | None = None


class ItemUpdateSerializer(AutoSchemas):
    name: str | None = None
    description: str | None = None


class ItemFilter(FilterSet):
    model = Item
    name__icontains: str | None = None


app = FastAPI()
router = APIRouter()


class ItemViewSet(CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet):
    router = router
    prefix = "/api/items"
    queryset = Item
    lookup_field = "id"
    filter_class = ItemFilter
    ordering = ["-created_at"]
    ordering_fields = ["id", "name", "created_at"]
    search_fields = ["name", "description"]
    pagination_class = LimitOffsetPagination
    serializer_class = ItemSerializer
    serializer_create_class = ItemCreateSerializer
    serializer_update_class = ItemUpdateSerializer


app.include_router(router)
register_exception_handlers(app)
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["__main__"]},  # 按你的模块路径调整
    generate_schemas=True,
)
```

生成的路由：

| 方法 | 路径 |
|------|------|
| GET | `/api/items/` |
| POST | `/api/items/` |
| GET | `/api/items/{id}/` |
| PUT / PATCH | `/api/items/{id}/` |
| DELETE | `/api/items/{id}/` |
| POST / PUT / DELETE | `/api/items/batch/` |

查询示例：

```text
GET /api/items/?name__icontains=foo&ordering=-name&search=bar&limit=10&offset=0
```

完整双资源示例（机构隔离、多表 create）：[`fast_generic_api/example/`](fast_generic_api/example/)

```bash
cd fast_generic_api/example
python main.py
# 打开 http://127.0.0.1:8000/docs
```

## 项目结构

```text
fast_generic_api/
├── backends/           # BaseBackend / Tortoise / SQLAlchemy
├── core/
│   ├── exceptions.py   # 异常 + 统一错误码 + 校验信封
│   ├── filter.py       # 声明式 FilterSet
│   ├── pagination.py   # LimitOffset / PageNumber
│   ├── permissions.py  # AllowAny / IsAuthenticated / ...
│   ├── response.py     # Response + Envelope
│   ├── schemas.py      # AutoSchemas（Meta.fields / exclude）
│   ├── serializers.py  # ModelSerializer（Tortoise）
│   ├── throttling.py   # 轻量节流
│   └── status.py
├── decorator.py        # @action / @api_meta
├── generics.py         # GenericAPIView + 组合 ViewSet
├── mixins.py           # CRUD + batch mixins
└── example/            # Item + Note 活文档
docs/
├── ERROR_CODES.md
├── HOOKS.md
└── MIGRATION.md
tests/
```

## 响应信封

```json
{
  "code": 200,
  "status": "success",
  "data": { "...": "..." },
  "msg": "OK"
}
```

| 场景 | HTTP | 业务 `code` |
|------|------|-------------|
| 成功 | 200 / 201 / 204 | 200 |
| 业务校验失败 | 400 | 40000 |
| 节流 | 400 | 40029 |
| 权限不足 | 403 | 40300 |
| 未找到 | 404 | 40400 |
| Schema 校验 | 422 | 42200 |

详见 [docs/ERROR_CODES.md](docs/ERROR_CODES.md)。

## Mixin 一览

| Mixin | 方法 | 路径 |
|-------|------|------|
| CreateModelMixin | POST | `/{prefix}/` |
| ListModelMixin | GET | `/{prefix}/` |
| RetrieveModelMixin | GET | `/{prefix}/{lookup}/` |
| UpdateModelMixin | PUT | `/{prefix}/{lookup}/` |
| PartialUpdateModelMixin | PATCH | `/{prefix}/{lookup}/` |
| DestroyModelMixin | DELETE | `/{prefix}/{lookup}/` |
| CreateManyMixin | POST | `/{prefix}/batch/` body: `{"items":[...]}` |
| UpdateManyMixin | PUT | `/{prefix}/batch/` body: `{"items":[{"id":1,...}]}` |
| DestroyManyMixin | DELETE | `/{prefix}/batch/` body `{"ids":[...]}` 或 `?ids=1,2` |

组合类：`CustomViewSet`（全量 CRUD）、`ListCreateViewSet`、`RetrieveUpdateDestroyViewSet` 等见 `generics.py`。

## GenericAPIView 常用配置

| 属性 | 说明 | 默认 |
|------|------|------|
| `router` / `prefix` | 路由注册 | 必填 |
| `queryset` | 模型类 | 必填 |
| `lookup_field` | 路径查找字段 | `"pk"` |
| `backend` / `backend_provider` | ORM 适配 / 每请求注入 | Tortoise |
| `serializer_*_class` | 按 action 切输入输出 | — |
| `filter_class` | FilterSet | None |
| `pagination_class` / `force_pagination` | 分页 | None / False |
| `ordering` / `ordering_fields` | 默认排序与白名单 | `[]` / None |
| `search_fields` | `?search=` 字段 | `[]` |
| `permission_classes` | 业务权限 | `[]` |
| `permissions` | FastAPI 认证 Depends | `[]` |
| `throttle_classes` | 节流 | `[]` |
| `batch_max_size` | 批量上限 | 100 |
| `select_related` / `prefetch_related` | 关联优化 | `[]` |
| `atomic_actions` | 写操作事务 | True |
| `envelope_response` | OpenAPI 信封 | True |

可覆盖钩子见 [docs/HOOKS.md](docs/HOOKS.md)。

## 自定义 Action

```python
from fastapi import Request
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action

class ItemViewSet(...):
    @action(detail=True, methods=["POST"], url_path="toggle-active")
    async def toggle_active(self, request: Request) -> Response:
        obj = await self.get_object()
        obj.is_active = not obj.is_active
        await self.backend.save(obj)
        return Response(self.get_serializer(obj))
```

- `detail=True` → `/{prefix}/{lookup}/toggle-active/`
- `detail=False` → `/{prefix}/toggle-active/`

## 过滤

```python
class ItemFilter(FilterSet):
    model = Item
    name__icontains: str | None = None
    is_active: bool | None = None
    # 旧版回调仍兼容
    filters = {
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }
```

## 排序 / 搜索 / 批量上限

```python
class ItemViewSet(...):
    ordering = ["-created_at"]
    ordering_fields = ["id", "name", "created_at"]
    search_fields = ["name", "description"]
    batch_max_size = 100
    force_pagination = True
```

- `GET .../?ordering=-name,id`
- `GET .../?search=apple`
- 非法 ordering / 超限 batch → `400` + `code=40000`

## 权限

```python
from fastapi import Depends
from fast_generic_api.core.permissions import BasePermission

class IsOwner(BasePermission):
    async def has_object_permission(self, request, obj) -> bool:
        return getattr(obj, "owner_id", None) == getattr(request.user, "id", None)

class ItemViewSet(...):
    permissions = [Depends(get_current_user)]  # 认证
    permission_classes = [IsOwner]             # 业务/对象权限
```

## 事务与多表写入

写操作默认在 `backend.in_transaction()` 中。批量任一条失败整批回滚。

```python
class ItemViewSet(...):
    atomic_actions = True  # 默认

    async def perform_create(self, data):
        payload = self.serialize_input_data(data)
        notes = payload.pop("notes", [])
        item = await self.backend.create(Item, **payload)
        for content in notes:
            await self.backend.create(Note, item_id=item.id, content=content)
        return item
```

## 多 ORM

默认 Tortoise：

```python
from fast_generic_api.backends import tortoise_backend

class ItemViewSet(...):
    backend = tortoise_backend  # 可省略
```

SQLAlchemy 2.x async：

```python
from fast_generic_api.backends import SQLAlchemyBackend

async def sa_backend():
    session = SessionLocal()
    return SQLAlchemyBackend(session)

class ItemViewSet(...):
    queryset = SAItem
    backend_provider = sa_backend
```

测试见 `tests/test_sqlalchemy_backend.py`。

## ModelSerializer / 字段裁剪

```python
from fast_generic_api.core.serializers import ModelSerializer
from fast_generic_api.core.schemas import AutoSchemas

class ItemSerializer(ModelSerializer):
    class Meta:
        model = Item
        fields = ("id", "name", "description")
        read_only_fields = ("id",)

class ItemListSerializer(AutoSchemas):
    id: int
    name: str
    class Meta:
        fields = ("id", "name")
```

> `ModelSerializer` 当前按 Tortoise `_meta` 生成；SQLAlchemy 建议手写 Pydantic。

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/ERROR_CODES.md](docs/ERROR_CODES.md) | 业务错误码 |
| [docs/HOOKS.md](docs/HOOKS.md) | 可覆盖钩子与类属性 |
| [docs/MIGRATION.md](docs/MIGRATION.md) | 版本迁移 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 |
| [ROADMAP.md](ROADMAP.md) | 1.x 方向 |

## 测试

```bash
pip install -e ".[test]"
pytest tests/ -q --cov=fast_generic_api
```

## 许可证

MIT — 见 [LICENSE](LICENSE)
