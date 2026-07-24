# 🚀 Fast Generic API

<div align="center">

**一个功能强大、设计优雅的 FastAPI 自动化 API 框架，提供类似 Django REST Framework 的体验**

**简体中文** | [English](README.en.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tortoise ORM](https://img.shields.io/badge/Tortoise%20ORM-0.20+-orange.svg)](https://tortoise-orm.readthedocs.io/)
[![PyPI](https://img.shields.io/badge/PyPI-1.0.0-blue.svg)](https://pypi.org/project/fast-generic-api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[📖 快速开始](#-快速开始) • [🏗️ 核心功能](#-核心功能) • [📚 API参考](#-api参考) • [🔧 高级配置](#-高级配置) • [🤝 贡献](#-贡献)

</div>

## 🌟 为什么选择 Fast Generic API？

Fast Generic API 是一个专为 FastAPI 设计的自动化 API 框架，提供类似 Django REST Framework 的开发体验，让你能够快速构建高质量的 API 服务。支持 **Tortoise ORM（默认）** 与 **SQLAlchemy 2.x async（可选）**。

<div align="center">

| 🎯 **CRUD自动化** | ⚡ **快速开发** | 🛡️ **类型安全** | 📈 **扩展性强** |
|:---:|:---:|:---:|:---:|
| 内置完整 CRUD + 批量操作 | 几行代码即可创建 API | 基于 Pydantic 和 Python 类型注解 | Backend 抽象，易于扩展 |

</div>

当前版本：**1.0.0**（公开 API 冻结，破坏性变更走 major）

## ✨ 核心功能

### 🔧 CRUD 操作自动化
- **CreateModelMixin** - 创建资源
- **ListModelMixin** - 列表查询（支持过滤、搜索、排序、分页）
- **RetrieveModelMixin** - 详情查询
- **UpdateModelMixin** - 完整更新
- **PartialUpdateModelMixin** - 部分更新
- **DestroyModelMixin** - 软删除（无 `is_deleted` 时物理删除）
- **CreateManyMixin / UpdateManyMixin / DestroyManyMixin** - 批量操作 `/batch/`

### 📦 通用 API 视图
- **GenericAPIView** - 统一的 API 视图基类
- **自动路由注册** - RESTful：`/` 与 `/{lookup}/`
- **@action** - 自定义 detail / collection 路由
- **权限控制** - `permissions`（认证 Depends）+ `permission_classes`（业务权限）
- **序列化器支持** - 按 action 切换 list/create/update/retrieve serializer

### 🌐 响应处理
- **统一响应信封** - `{code, status, data, msg}`
- **OpenAPI Envelope[T]** - `/docs` 与真实 JSON 结构对齐
- **分页响应** - LimitOffset / PageNumber
- **错误处理** - 统一业务码（见 [docs/ERROR_CODES.md](docs/ERROR_CODES.md)）

### 🏗️ 高级功能
- **声明式 FilterSet** - Pydantic 风格查询参数，进 OpenAPI
- **排序白名单** - `?ordering=` + `ordering_fields`
- **搜索** - `?search=` + `search_fields`
- **分页** - LimitOffset / PageNumber，可 `force_pagination`
- **多 ORM Backend** - Tortoise 默认 / SQLAlchemy 可选
- **事务** - 写操作默认 `in_transaction()`，`atomic_actions` 可关
- **节流** - 可选 `throttle_classes`
- **关联优化** - `select_related` / `prefetch_related`

## 🛠️ 技术栈

| 组件 | 技术选型 | 版本要求 |
|------|----------|----------|
| **Web框架** | FastAPI | 0.100+ |
| **ORM** | Tortoise ORM（默认）/ SQLAlchemy 2.x async（可选） | Tortoise 0.20+ |
| **序列化** | Pydantic | 2.0+ |
| **数据库** | 支持多种数据库 | - |
| **Python版本** | Python | 3.11+ |

## 📁 项目结构

```text
fast_generic_api/
├── __init__.py                 # 包初始化（VERSION=1.0.0）
├── mixins.py                   # CRUD + 批量混入类
├── generics.py                 # GenericAPIView / 组合 ViewSet
├── decorator.py                # @action / @api_meta
├── backends/                   # ORM 适配层
│   ├── base.py
│   ├── tortoise_orm.py
│   └── sqlalchemy_orm.py
├── core/                       # 核心模块
│   ├── exceptions.py           # 异常 + 错误码 + 校验信封
│   ├── filter.py               # 声明式 FilterSet
│   ├── pagination.py           # LimitOffset / PageNumber
│   ├── permissions.py          # 权限基类
│   ├── response.py             # Response + Envelope
│   ├── schemas.py              # AutoSchemas
│   ├── serializers.py          # ModelSerializer（Tortoise）
│   ├── throttling.py           # 轻量节流
│   └── status.py               # HTTP 状态码
├── example/                    # 示例（Item + Note）
│   ├── main.py
│   ├── model.py
│   └── serializers.py
docs/
├── ERROR_CODES.md
├── HOOKS.md
└── MIGRATION.md
tests/                          # pytest 套件
```

## 🚀 快速开始

### ⚡ 安装

```bash
# PyPI
pip install fast-generic-api==1.0.0

# 可选 SQLAlchemy
pip install "fast-generic-api[sqlalchemy]"

# 从源码
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_generic_api
pip install -e ".[test]"
```

### 💻 基础使用

#### 1. 创建模型

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

#### 2. 创建序列化器

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

#### 3. 创建 API 视图

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

#### 4. 启动应用

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

生成路由：

| 方法 | 路径 |
|------|------|
| GET / POST | `/api/users/` |
| GET / PUT / PATCH / DELETE | `/api/users/{id}/` |
| POST / PUT / DELETE | `/api/users/batch/` |

完整双资源示例（机构隔离、多表写入）：

```bash
cd fast_generic_api/example
python main.py
# 打开 http://127.0.0.1:8000/docs
```

## 📚 API 参考

### 可用的 Mixin 类

#### CreateModelMixin
- **方法**: `POST /{prefix}/`
- **功能**: 创建新资源
- **请求体**: 根据 `serializer_create_class` 定义
- **响应**: 创建的资源详情（201）

#### CreateManyMixin
- **方法**: `POST /{prefix}/batch/`
- **功能**: 批量创建，事务内逐条 `perform_create`
- **请求体**: `{"items": [{...}, {...}]}`
- **上限**: `batch_max_size`（默认 100）

#### ListModelMixin
- **方法**: `GET /{prefix}/`
- **功能**: 获取资源列表
- **查询参数**:
  - `limit` / `offset` 或 `page` / `page_size`
  - `ordering`（白名单字段）
  - `search`（`search_fields` OR 模糊）
  - FilterSet 声明字段
- **响应**: 列表或分页结构

#### RetrieveModelMixin
- **方法**: `GET /{prefix}/{lookup_field}/`
- **功能**: 获取单个资源详情

#### UpdateModelMixin
- **方法**: `PUT /{prefix}/{lookup_field}/`
- **功能**: 完整更新资源

#### UpdateManyMixin
- **方法**: `PUT /{prefix}/batch/`
- **功能**: 批量更新
- **请求体**: `{"items": [{"id": 1, "name": "new"}]}`（每项含 lookup）

#### PartialUpdateModelMixin
- **方法**: `PATCH /{prefix}/{lookup_field}/`
- **功能**: 部分更新资源

#### DestroyModelMixin
- **方法**: `DELETE /{prefix}/{lookup_field}/`
- **功能**: 软删除（`is_deleted=True`）或物理删除
- **响应**: 204 No Content

#### DestroyManyMixin
- **方法**: `DELETE /{prefix}/batch/`
- **功能**: 批量删除
- **请求体**: `{"ids": [1, 2]}` 或查询参数 `?ids=1,2`

### GenericAPIView 配置

| 属性 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `router` | APIRouter | FastAPI 路由实例 | None |
| `prefix` | str | API 路径前缀 | None |
| `queryset` | Model | 数据库模型 | None |
| `serializer_class` | BaseModel | 默认序列化器 | None |
| `serializer_create_class` | BaseModel | 创建序列化器 | None |
| `serializer_update_class` | BaseModel | 更新序列化器 | None |
| `serializer_list_class` | BaseModel | 列表响应序列化器 | None |
| `serializer_retrieve_class` | BaseModel | 详情响应序列化器 | None |
| `lookup_field` | str | 资源查找字段 | `"pk"` |
| `ordering` | list | 默认排序字段 | `[]` |
| `ordering_fields` | list | `?ordering=` 白名单 | None |
| `search_fields` | list | `?search=` 字段 | `[]` |
| `pagination_class` | class | 分页类 | None |
| `force_pagination` | bool | 强制分页 | False |
| `filter_class` | class | 过滤类 | None |
| `permissions` | list | FastAPI 认证 Depends | `[]` |
| `permission_classes` | list | 业务权限类 | `[]` |
| `throttle_classes` | list | 节流类 | `[]` |
| `select_related` | list | 外键关联优化 | `[]` |
| `prefetch_related` | list | 反向/M2M 预取 | `[]` |
| `backend` | BaseBackend | ORM 适配 | Tortoise |
| `backend_provider` | callable | 每请求注入 backend | None |
| `batch_max_size` | int | 批量上限 | 100 |
| `atomic_actions` | bool | 写操作事务 | True |
| `envelope_response` | bool | OpenAPI 信封 | True |

## 🔧 高级配置

### 自定义 Action

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

### 自定义过滤

```python
from fast_generic_api.core.filter import FilterSet

class UserFilter(FilterSet):
    model = User
    username__icontains: str | None = None
    is_active: bool | None = None
    # 旧版回调仍兼容
    filters = {
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }

class UserViewSet(...):
    filter_class = UserFilter
```

### 排序 / 搜索 / 批量上限

```python
class UserViewSet(...):
    ordering = ["-created_at"]
    ordering_fields = ["id", "username", "created_at"]
    search_fields = ["username", "email"]
    batch_max_size = 100
    force_pagination = True
```

- `GET /api/users/?ordering=-username&search=alice`
- 非法字段或超限 → HTTP 400，业务码 `40000`

### ModelSerializer 与字段裁剪

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

> `ModelSerializer` 当前面向 Tortoise；SQLAlchemy 建议手写 Pydantic。

### 自定义分页

```python
from fast_generic_api.core.pagination import LimitOffsetPagination, PageNumberPagination

class CustomPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 500

class UserViewSet(...):
    pagination_class = CustomPagination  # 或 PageNumberPagination
```

### 权限控制

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
    permissions = [Depends(get_current_active_user)]  # 认证
    permission_classes = [IsOwner]                    # 业务/对象权限
```

### 事务说明

写操作默认包裹在 `backend.in_transaction()` 中，包括：

- `create` / `update` / `partial_update` / `destroy`
- `create_many` / `update_many` / `destroy_many`

批量中任意一条失败会整体回滚。可关闭：

```python
class UserViewSet(...):
    atomic_actions = False
```

多表写入推荐重写 `perform_create` / `perform_update`：

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

### 多 ORM Backend（Tortoise / SQLAlchemy）

```python
from fast_generic_api.backends import tortoise_backend

class ItemViewSet(...):
    backend = tortoise_backend  # 默认，可省略
```

切换 SQLAlchemy 2.x async：

```bash
pip install "fast-generic-api[sqlalchemy]"
```

```python
from fast_generic_api.backends import SQLAlchemyBackend
from fast_generic_api.generics import CustomViewSet

async def sa_backend():
    session = SessionLocal()
    return SQLAlchemyBackend(session)

class ItemViewSet(CustomViewSet):
    queryset = SAItem
    lookup_field = "id"
    backend_provider = sa_backend  # 每请求注入
```

测试示例：`tests/test_sqlalchemy_backend.py`

### 响应信封与错误码

```json
{
  "code": 200,
  "status": "success",
  "data": {},
  "msg": "OK"
}
```

| 场景 | HTTP | 业务 code |
|------|------|-----------|
| 成功 | 200/201/204 | 200 |
| 业务校验 | 400 | 40000 |
| 节流 | 400 | 40029 |
| 权限 | 403 | 40300 |
| 未找到 | 404 | 40400 |
| Schema 校验 | 422 | 42200 |

详见 [docs/ERROR_CODES.md](docs/ERROR_CODES.md)。

### 文档索引

- [docs/ERROR_CODES.md](docs/ERROR_CODES.md) — 错误码
- [docs/HOOKS.md](docs/HOOKS.md) — 可覆盖钩子
- [docs/MIGRATION.md](docs/MIGRATION.md) — 迁移指南
- [CHANGELOG.md](CHANGELOG.md) — 变更记录
- [ROADMAP.md](ROADMAP.md) — 1.x 方向

## 📦 依赖

- **FastAPI** - Web 框架
- **Tortoise ORM** - 默认异步 ORM
- **Pydantic** - 数据验证与序列化
- **SQLAlchemy**（可选 extra）- 第二 ORM

## 🧪 测试

```bash
pip install -e ".[test]"
pytest tests/ -q --cov=fast_generic_api
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件

## 💖 致谢

- 感谢 [FastAPI](https://fastapi.tiangolo.com/) 提供优秀的 Web 框架
- 感谢 [Django REST Framework](https://www.django-rest-framework.org/) 提供设计灵感
- 感谢所有使用和支持这个项目的开发者！
