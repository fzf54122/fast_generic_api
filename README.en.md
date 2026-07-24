# fast_generic_api

<div align="center">

**DRF-style generic CRUD for FastAPI**  
Tortoise ORM (default) · SQLAlchemy 2.x async (optional) · unified response envelope · tests

[简体中文](README.md) | **English**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PyPI](https://img.shields.io/badge/PyPI-1.0.0-blue.svg)](https://pypi.org/project/fast-generic-api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## Features

| Feature | Notes |
|---------|--------|
| RESTful CRUD | list / create / retrieve / update / partial_update / destroy |
| Batch ops | `CreateManyMixin` / `UpdateManyMixin` / `DestroyManyMixin` → `/batch/` |
| `@action` | Custom detail / collection routes |
| Declarative FilterSet | Pydantic-style query params, OpenAPI-visible |
| Ordering / search | `?ordering=` allowlist, `?search=` + `search_fields` |
| Pagination | `LimitOffsetPagination` / `PageNumberPagination`, optional `force_pagination` |
| Permissions | `permission_classes` + FastAPI `permissions` dependencies |
| Soft / hard delete | Soft-delete when `is_deleted` exists, else hard delete |
| Multi-ORM | `TortoiseBackend` default, `SQLAlchemyBackend` optional |
| Response envelope | `{code,status,data,msg}`, OpenAPI `Envelope[T]` |
| Transactions | Write ops default to `backend.in_transaction()` |
| Throttling | Optional `throttle_classes` (in-process) |

Current version: **1.0.0** (public API frozen; breaking changes go major)

## Install

```bash
pip install fast-generic-api==1.0.0

# Optional SQLAlchemy extra
pip install "fast-generic-api[sqlalchemy]"
```

Development:

```bash
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_generic_api
pip install -e ".[test]"
pytest tests/ -q
```

## Quick start

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
    modules={"models": ["__main__"]},  # adjust to your module path
    generate_schemas=True,
)
```

Routes:

| Method | Path |
|--------|------|
| GET | `/api/items/` |
| POST | `/api/items/` |
| GET | `/api/items/{id}/` |
| PUT / PATCH | `/api/items/{id}/` |
| DELETE | `/api/items/{id}/` |
| POST / PUT / DELETE | `/api/items/batch/` |

Query example:

```text
GET /api/items/?name__icontains=foo&ordering=-name&search=bar&limit=10&offset=0
```

Full dual-resource example (tenant isolation, multi-table create): [`fast_generic_api/example/`](fast_generic_api/example/)

```bash
cd fast_generic_api/example
python main.py
# open http://127.0.0.1:8000/docs
```

## Project layout

```text
fast_generic_api/
├── backends/           # BaseBackend / Tortoise / SQLAlchemy
├── core/
│   ├── exceptions.py
│   ├── filter.py
│   ├── pagination.py
│   ├── permissions.py
│   ├── response.py     # Response + Envelope
│   ├── schemas.py      # AutoSchemas
│   ├── serializers.py  # ModelSerializer (Tortoise)
│   ├── throttling.py
│   └── status.py
├── decorator.py        # @action / @api_meta
├── generics.py
├── mixins.py
└── example/            # Item + Note living docs
docs/
├── ERROR_CODES.md
├── HOOKS.md
└── MIGRATION.md
tests/
```

## Response envelope

```json
{
  "code": 200,
  "status": "success",
  "data": { "...": "..." },
  "msg": "OK"
}
```

| Case | HTTP | Business `code` |
|------|------|-----------------|
| Success | 200 / 201 / 204 | 200 |
| Business validation | 400 | 40000 |
| Throttled | 400 | 40029 |
| Permission denied | 403 | 40300 |
| Not found | 404 | 40400 |
| Schema validation | 422 | 42200 |

See [docs/ERROR_CODES.md](docs/ERROR_CODES.md).

## Mixins

| Mixin | Method | Path |
|-------|--------|------|
| CreateModelMixin | POST | `/{prefix}/` |
| ListModelMixin | GET | `/{prefix}/` |
| RetrieveModelMixin | GET | `/{prefix}/{lookup}/` |
| UpdateModelMixin | PUT | `/{prefix}/{lookup}/` |
| PartialUpdateModelMixin | PATCH | `/{prefix}/{lookup}/` |
| DestroyModelMixin | DELETE | `/{prefix}/{lookup}/` |
| CreateManyMixin | POST | `/{prefix}/batch/` body `{"items":[...]}` |
| UpdateManyMixin | PUT | `/{prefix}/batch/` body `{"items":[{"id":1,...}]}` |
| DestroyManyMixin | DELETE | `/{prefix}/batch/` body `{"ids":[...]}` or `?ids=1,2` |

Combinations: `CustomViewSet`, `ListCreateViewSet`, `RetrieveUpdateDestroyViewSet`, etc. in `generics.py`.

## Common GenericAPIView settings

| Attribute | Purpose | Default |
|-----------|---------|---------|
| `router` / `prefix` | Route registration | required |
| `queryset` | Model class | required |
| `lookup_field` | Path lookup field | `"pk"` |
| `backend` / `backend_provider` | ORM adapter / per-request inject | Tortoise |
| `serializer_*_class` | Per-action serializers | — |
| `filter_class` | FilterSet | None |
| `pagination_class` / `force_pagination` | Pagination | None / False |
| `ordering` / `ordering_fields` | Default order + allowlist | `[]` / None |
| `search_fields` | `?search=` fields | `[]` |
| `permission_classes` | Business permissions | `[]` |
| `permissions` | FastAPI auth Depends | `[]` |
| `throttle_classes` | Throttles | `[]` |
| `batch_max_size` | Batch limit | 100 |
| `select_related` / `prefetch_related` | Relation loading | `[]` |
| `atomic_actions` | Wrap writes in transaction | True |
| `envelope_response` | OpenAPI envelope | True |

Override hooks: [docs/HOOKS.md](docs/HOOKS.md).

## Custom actions

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

## Filtering

```python
class ItemFilter(FilterSet):
    model = Item
    name__icontains: str | None = None
    is_active: bool | None = None
    # Legacy callbacks still work
    filters = {
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }
```

## Ordering / search / batch limit

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
- Invalid ordering / oversized batch → HTTP `400`, business `code=40000`

## Permissions

```python
from fastapi import Depends
from fast_generic_api.core.permissions import BasePermission

class IsOwner(BasePermission):
    async def has_object_permission(self, request, obj) -> bool:
        return getattr(obj, "owner_id", None) == getattr(request.user, "id", None)

class ItemViewSet(...):
    permissions = [Depends(get_current_user)]  # auth
    permission_classes = [IsOwner]             # object-level
```

## Transactions & multi-table writes

Writes run inside `backend.in_transaction()` by default. Any failure in a batch rolls back the whole batch.

```python
class ItemViewSet(...):
    async def perform_create(self, data):
        payload = self.serialize_input_data(data)
        notes = payload.pop("notes", [])
        item = await self.backend.create(Item, **payload)
        for content in notes:
            await self.backend.create(Note, item_id=item.id, content=content)
        return item
```

## Multi-ORM

Tortoise (default):

```python
from fast_generic_api.backends import tortoise_backend

class ItemViewSet(...):
    backend = tortoise_backend  # optional
```

SQLAlchemy 2.x async:

```python
from fast_generic_api.backends import SQLAlchemyBackend

async def sa_backend():
    session = SessionLocal()
    return SQLAlchemyBackend(session)

class ItemViewSet(...):
    queryset = SAItem
    backend_provider = sa_backend
```

See `tests/test_sqlalchemy_backend.py`.

## ModelSerializer / field control

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

> `ModelSerializer` currently targets Tortoise `_meta`. For SQLAlchemy, write Pydantic models by hand.

## Docs index

| Doc | Content |
|-----|---------|
| [docs/ERROR_CODES.md](docs/ERROR_CODES.md) | Business error codes |
| [docs/HOOKS.md](docs/HOOKS.md) | Override hooks & class attrs |
| [docs/MIGRATION.md](docs/MIGRATION.md) | Version migration |
| [CHANGELOG.md](CHANGELOG.md) | Changelog |
| [ROADMAP.md](ROADMAP.md) | 1.x direction |

## Tests

```bash
pip install -e ".[test]"
pytest tests/ -q --cov=fast_generic_api
```

## License

MIT — see [LICENSE](LICENSE)
