# 🚀 Fast Generic API

<div align="center">

**A powerful and elegantly designed FastAPI automation API framework with a Django REST Framework-like experience**

[简体中文](README.md) | **English**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tortoise ORM](https://img.shields.io/badge/Tortoise%20ORM-0.20+-orange.svg)](https://tortoise-orm.readthedocs.io/)
[![PyPI](https://img.shields.io/badge/PyPI-1.0.1-blue.svg)](https://pypi.org/project/fast-generic-api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[📖 Quick Start](#-quick-start) • [🏗️ Core Features](#-core-features) • [📚 API Reference](#-api-reference) • [🔧 Advanced Configuration](#-advanced-configuration) • [🤝 Contribution](#-contribution)

</div>

## 🌟 Why Choose Fast Generic API?

Fast Generic API is an automation API framework for FastAPI with a DRF-like developer experience. It supports **Tortoise ORM (default)** and **SQLAlchemy 2.x async (optional)**.

<div align="center">

| 🎯 **CRUD Automation** | ⚡ **Rapid Development** | 🛡️ **Type Safety** | 📈 **Extensibility** |
|:---:|:---:|:---:|:---:|
| Full CRUD + batch ops | Create APIs in a few lines | Pydantic + type hints | Backend abstraction |

</div>

Current version: **1.0.1** (public API frozen; breaking changes go major)

## ✨ Core Features

### 🔧 CRUD Automation
- **CreateModelMixin** - Create resources
- **ListModelMixin** - List with filter / search / ordering / pagination
- **RetrieveModelMixin** - Detail
- **UpdateModelMixin** - Full update
- **PartialUpdateModelMixin** - Partial update
- **DestroyModelMixin** - Soft delete (or hard delete without `is_deleted`)
- **CreateMany / UpdateMany / DestroyMany** - Batch via `/batch/`

### 📦 Generic API Views
- **GenericAPIView** - Unified base view
- **Automatic routing** - RESTful `/` and `/{lookup}/`
- **@action** - Custom detail / collection routes
- **Permissions** - FastAPI `permissions` + business `permission_classes`
- **Serializers** - Per-action list / create / update / retrieve classes

### 🌐 Response Handling
- **Unified envelope** - `{code, status, data, msg}`
- **OpenAPI Envelope[T]** - Docs match real JSON
- **Pagination** - LimitOffset / PageNumber
- **Error codes** - See [docs/ERROR_CODES.md](docs/ERROR_CODES.md)

### 🏗️ Advanced Features
- **Declarative FilterSet** - Pydantic-style query params
- **Ordering allowlist** - `?ordering=` + `ordering_fields`
- **Search** - `?search=` + `search_fields`
- **Multi-ORM Backend** - Tortoise default / SQLAlchemy optional
- **Transactions** - Writes default to `in_transaction()`
- **Throttling** - Optional `throttle_classes`
- **Relation loading** - `select_related` / `prefetch_related`

## 🛠️ Technology Stack

| Component | Choice | Requirement |
|-----------|--------|-------------|
| **Web** | FastAPI | 0.100+ |
| **ORM** | Tortoise (default) / SQLAlchemy 2.x async (optional) | Tortoise 0.20+ |
| **Serialization** | Pydantic | 2.0+ |
| **Database** | Multiple backends | - |
| **Python** | Python | 3.11+ |

## 📁 Project Structure

```text
fast_generic_api/
├── __init__.py                 # VERSION=1.0.1
├── mixins.py                   # CRUD + batch mixins
├── generics.py                 # GenericAPIView / ViewSet combos
├── decorator.py                # @action / @api_meta
├── backends/                   # ORM adapters
│   ├── base.py
│   ├── tortoise_orm.py
│   └── sqlalchemy_orm.py
├── core/
│   ├── exceptions.py
│   ├── filter.py
│   ├── pagination.py
│   ├── permissions.py
│   ├── response.py
│   ├── schemas.py
│   ├── serializers.py
│   ├── throttling.py
│   └── status.py
├── example/                    # Item + Note living docs
│   ├── main.py
│   ├── model.py
│   └── serializers.py
docs/
├── ERROR_CODES.md
├── HOOKS.md
└── MIGRATION.md
tests/
```

## 🚀 Quick Start

### ⚡ Install

```bash
pip install fast-generic-api==1.0.1

# Optional SQLAlchemy
pip install "fast-generic-api[sqlalchemy]"

# From source
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_generic_api
pip install -e ".[test]"
```

### 💻 Basic Usage

#### 1. Create Model

```python
from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    is_deleted = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
```

#### 2. Create Serializers

```python
from typing import Optional
from fast_generic_api.core.schemas import AutoSchemas

class UserCreate(AutoSchemas):
    username: str
    email: str

class UserUpdate(AutoSchemas):
    username: Optional[str] = None
    email: Optional[str] = None

class UserInDB(AutoSchemas):
    id: int
    username: str
    email: str
    is_deleted: bool
```

#### 3. Create API View

```python
from fastapi import APIRouter
from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination

router = APIRouter(tags=["Users"])

class UserFilter(FilterSet):
    model = User
    username__icontains: str | None = None

class UserViewSet(CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet):
    router = router
    prefix = "/api/users"
    queryset = User
    lookup_field = "id"
    filter_class = UserFilter
    ordering = ["-created_at"]
    ordering_fields = ["id", "username", "created_at"]
    search_fields = ["username", "email"]
    pagination_class = LimitOffsetPagination
    serializer_class = UserInDB
    serializer_create_class = UserCreate
    serializer_update_class = UserUpdate
```

#### 4. Start App

```python
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fast_generic_api.core.exceptions import register_exception_handlers

app = FastAPI(title="Fast Generic API Example")
app.include_router(router)
register_exception_handlers(app)

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Routes:

| Method | Path |
|--------|------|
| GET / POST | `/api/users/` |
| GET / PUT / PATCH / DELETE | `/api/users/{id}/` |
| POST / PUT / DELETE | `/api/users/batch/` |

Full dual-resource example:

```bash
cd fast_generic_api/example
python main.py
# open http://127.0.0.1:8000/docs
```

## 📚 API Reference

### Available Mixins

#### CreateModelMixin
- **Method**: `POST /{prefix}/`
- **Body**: `serializer_create_class`
- **Response**: created resource (201)

#### CreateManyMixin
- **Method**: `POST /{prefix}/batch/`
- **Body**: `{"items": [{...}, {...}]}`
- **Limit**: `batch_max_size` (default 100)

#### ListModelMixin
- **Method**: `GET /{prefix}/`
- **Query**: `limit`/`offset` or `page`/`page_size`, `ordering`, `search`, FilterSet fields

#### RetrieveModelMixin
- **Method**: `GET /{prefix}/{lookup_field}/`

#### UpdateModelMixin
- **Method**: `PUT /{prefix}/{lookup_field}/`

#### UpdateManyMixin
- **Method**: `PUT /{prefix}/batch/`
- **Body**: `{"items": [{"id": 1, "name": "new"}]}`

#### PartialUpdateModelMixin
- **Method**: `PATCH /{prefix}/{lookup_field}/`

#### DestroyModelMixin
- **Method**: `DELETE /{prefix}/{lookup_field}/`
- **Response**: 204 No Content

#### DestroyManyMixin
- **Method**: `DELETE /{prefix}/batch/`
- **Body**: `{"ids": [1, 2]}` or `?ids=1,2`

### GenericAPIView Configuration

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `router` | APIRouter | FastAPI router | None |
| `prefix` | str | Path prefix | None |
| `queryset` | Model | Model class | None |
| `serializer_class` | BaseModel | Default serializer | None |
| `serializer_create_class` | BaseModel | Create serializer | None |
| `serializer_update_class` | BaseModel | Update serializer | None |
| `serializer_list_class` | BaseModel | List response serializer | None |
| `serializer_retrieve_class` | BaseModel | Detail response serializer | None |
| `lookup_field` | str | Lookup field | `"pk"` |
| `ordering` | list | Default ordering | `[]` |
| `ordering_fields` | list | Ordering allowlist | None |
| `search_fields` | list | Search fields | `[]` |
| `pagination_class` | class | Pagination class | None |
| `force_pagination` | bool | Force pagination | False |
| `filter_class` | class | FilterSet | None |
| `permissions` | list | FastAPI auth Depends | `[]` |
| `permission_classes` | list | Business permissions | `[]` |
| `throttle_classes` | list | Throttles | `[]` |
| `select_related` | list | Join optimization | `[]` |
| `prefetch_related` | list | Prefetch optimization | `[]` |
| `backend` | BaseBackend | ORM adapter | Tortoise |
| `backend_provider` | callable | Per-request backend | None |
| `batch_max_size` | int | Batch limit | 100 |
| `atomic_actions` | bool | Wrap writes in TX | True |
| `envelope_response` | bool | OpenAPI envelope | True |

## 🔧 Advanced Configuration

### Custom Action

```python
from fastapi import Request
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action

class UserViewSet(...):
    @action(detail=True, methods=["POST"], url_path="toggle-active")
    async def toggle_active(self, request: Request) -> Response:
        user = await self.get_object()
        user.is_active = not user.is_active
        await self.backend.save(user)
        return Response(self.get_serializer(user))
```

- `detail=True` → `/{prefix}/{lookup}/toggle-active/`
- `detail=False` → `/{prefix}/toggle-active/`

### Custom Filter

```python
from fast_generic_api.core.filter import FilterSet

class UserFilter(FilterSet):
    model = User
    username__icontains: str | None = None
    is_active: bool | None = None
    filters = {
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }
```

### Ordering / Search / Batch Limit

```python
class UserViewSet(...):
    ordering = ["-created_at"]
    ordering_fields = ["id", "username", "created_at"]
    search_fields = ["username", "email"]
    batch_max_size = 100
    force_pagination = True
```

### ModelSerializer & Field Control

```python
from fast_generic_api.core.serializers import ModelSerializer
from fast_generic_api.core.schemas import AutoSchemas

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = ("id",)

class UserListSerializer(AutoSchemas):
    id: int
    username: str
    class Meta:
        fields = ("id", "username")
```

### Pagination

```python
from fast_generic_api.core.pagination import LimitOffsetPagination, PageNumberPagination

class CustomPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 500
```

### Permissions

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fast_generic_api.core.exceptions import HTTPPermissionException
from fast_generic_api.core.permissions import BasePermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    if not is_valid_token(token):
        raise HTTPPermissionException
    return user

class IsOwner(BasePermission):
    async def has_object_permission(self, request, obj) -> bool:
        return obj.owner_id == request.user.id

class UserViewSet(...):
    permissions = [Depends(get_current_active_user)]
    permission_classes = [IsOwner]
```

### Transactions

Write operations run inside `backend.in_transaction()` by default (including batch mixins). Disable with `atomic_actions = False`. Prefer overriding `perform_create` / `perform_update` for multi-table writes.

### Multi-ORM Backend

```python
from fast_generic_api.backends import tortoise_backend, SQLAlchemyBackend

# Tortoise (default)
class ItemViewSet(...):
    backend = tortoise_backend

# SQLAlchemy
async def sa_backend():
    return SQLAlchemyBackend(SessionLocal())

class ItemViewSet(...):
    queryset = SAItem
    backend_provider = sa_backend
```

```bash
pip install "fast-generic-api[sqlalchemy]"
```

### Response Envelope & Error Codes

```json
{
  "code": 200,
  "status": "success",
  "data": {},
  "msg": "OK"
}
```

| Case | HTTP | Business code |
|------|------|---------------|
| Success | 200/201/204 | 200 |
| Business validation | 400 | 40000 |
| Throttled | 400 | 40029 |
| Permission | 403 | 40300 |
| Not found | 404 | 40400 |
| Schema validation | 422 | 42200 |

See [docs/ERROR_CODES.md](docs/ERROR_CODES.md).

### Docs Index

- [docs/ERROR_CODES.md](docs/ERROR_CODES.md)
- [docs/HOOKS.md](docs/HOOKS.md)
- [docs/MIGRATION.md](docs/MIGRATION.md)
- [CHANGELOG.md](CHANGELOG.md)
- [ROADMAP.md](ROADMAP.md)

## 📦 Dependencies

- **FastAPI**
- **Tortoise ORM** (default)
- **Pydantic**
- **SQLAlchemy** (optional extra)

## 🧪 Tests

```bash
pip install -e ".[test]"
pytest tests/ -q --cov=fast_generic_api
```

## 🤝 Contribution

1. Fork
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'feat: add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT — see [LICENSE](LICENSE)

## 💖 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- Everyone using and supporting this project
