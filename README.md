# 🚀 Fast Auto Framework

<div align="center">

**一个功能强大、设计优雅的FastAPI自动化API框架，提供类似Django REST Framework的体验**

**简体中文** | [English](README.en.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tortoise ORM](https://img.shields.io/badge/Tortoise%20ORM-0.20+-orange.svg)](https://tortoise-orm.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[📖 快速开始](#-快速开始) • [🏗️ 核心功能](#-核心功能) • [📚 API参考](#-api参考) • [🔧 高级配置](#-高级配置) • [🤝 贡献](#-贡献)

</div>

## 🌟 为什么选择 Fast Auto Framework？

Fast Auto Framework 是一个专为FastAPI设计的自动化API框架，提供了类似Django REST Framework的开发体验，让你能够快速构建高质量的API服务。

<div align="center">

| 🎯 **CRUD自动化** | ⚡ **快速开发** | 🛡️ **类型安全** | 📈 **扩展性强** |
|:---:|:---:|:---:|:---:|
| 内置完整CRUD操作 | 几行代码即可创建API | 基于Pydantic和Python类型注解 | 模块化设计，易于扩展 |

</div>

## ✨ 核心功能

### 🔧 CRUD操作自动化
- **CreateModelMixin** - 创建资源
- **ListModelMixin** - 列表查询（支持分页和过滤）
- **RetrieveModelMixin** - 详情查询
- **UpdateModelMixin** - 完整更新
- **PartialUpdateModelMixin** - 部分更新
- **DestroyModelMixin** - 软删除功能

### 📦 通用API视图
- **GenericAPIView** - 统一的API视图基类
- **自动路由注册** - 基于类属性的自动路由生成
- **权限控制** - 灵活的权限依赖注入
- **序列化器支持** - 支持不同操作使用不同序列化器

### 🌐 响应处理
- **统一响应格式** - 标准化的API响应结构
- **分页响应** - 内置分页信息
- **错误处理** - 统一的错误响应格式
- **JSON序列化** - 自动处理Pydantic和datetime类型

### 🏗️ 高级功能
- **过滤系统** - 灵活的查询过滤
- **分页支持** - LimitOffset分页机制
- **UUID支持** - 自定义UUID作为主键
- **排序功能** - 支持多字段排序

## 🛠️ 技术栈

| 组件 | 技术选型 | 版本要求 |
|------|----------|----------|
| **Web框架** | FastAPI | 0.100+ |
| **ORM** | Tortoise ORM | 0.20+ |
| **序列化** | Pydantic | 2.0+ |
| **数据库** | 支持多种数据库 | - |
| **Python版本** | Python | 3.11+ |

## 📁 项目结构

```
fast_generic_api/
├── __init__.py                 # 包初始化
├── mixins.py                   # CRUD混入类
├── generics.py                 # 通用API视图
├── core/                       # 核心模块
│   ├── __init__.py            # 核心模块初始化
│   ├── exceptions.py          # 自定义异常
│   ├── filter.py              # 过滤系统
│   ├── pagination.py          # 分页功能
│   ├── response.py            # 统一响应
│   └── status.py              # HTTP状态码
├── example/                    # 示例代码
│   ├── __init__.py            # 示例模块初始化
│   └── example.py             # 使用示例
└── README.md                   # 项目文档
```

## 🚀 快速开始

### ⚡ 安装依赖

```bash
# 克隆项目
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_generic_api

# 安装依赖
pip install fastapi tortoise-orm pydantic
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
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True
```

#### 3. 创建API视图

```python
from fastapi import APIRouter
from fast_generic_api.generics import GenericAPIView
from fast_generic_api import mixins
from models import User
from serializers import UserInDB, UserCreate, UserUpdate

# 创建路由
router = APIRouter(prefix="/api", tags=["Users"])

class UserViewSet(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 GenericAPIView):
    router = router
    prefix = "/users"
    queryset = User
    serializer_class = UserInDB
    serializer_create_class = UserCreate
    serializer_update_class = UserUpdate
    ordering = ["-created_at"]
    lookup_field = "id"
```

#### 4. 启动应用

```python
from fastapi import FastAPI
from api.views import router

app = FastAPI(title="Fast Auto Framework Example")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📚 API参考

### 可用的Mixin类

#### CreateModelMixin
- **方法**: `POST /{prefix}/`
- **功能**: 创建新资源
- **请求体**: 根据 `serializer_create_class` 定义
- **响应**: 创建的资源详情

#### CreateManyMixin
- **方法**: `POST /{prefix}/batch/`
- **功能**: 批量创建资源，事务内逐条调用 `perform_create`
- **请求体**: `{"items": [{...}, {...}]}`
- **响应**: 创建后的资源列表

#### ListModelMixin
- **方法**: `GET /{prefix}/`
- **功能**: 获取资源列表
- **查询参数**: 
  - `limit`: 每页数量（默认：10，最大：1000）
  - `offset`: 偏移量（默认：0）
  - 其他过滤字段
- **响应**: 分页的资源列表

#### RetrieveModelMixin
- **方法**: `GET /{prefix}/{lookup_field}/`
- **功能**: 获取单个资源详情
- **路径参数**: 
  - `{lookup_field}`: 资源标识符
- **响应**: 资源详情

#### UpdateModelMixin
- **方法**: `PUT /{prefix}/{lookup_field}/`
- **功能**: 完整更新资源
- **路径参数**: 
  - `{lookup_field}`: 资源标识符
- **请求体**: 根据 `serializer_update_class` 定义
- **响应**: 更新后的资源详情

#### UpdateManyMixin
- **方法**: `PUT /{prefix}/batch/`
- **功能**: 批量更新资源，事务内逐条调用 `perform_update`
- **请求体**: `{"items": [{"id": 1, "name": "new"}]}`，每项需包含 `lookup_field`
- **响应**: 更新后的资源列表

#### PartialUpdateModelMixin
- **方法**: `PATCH /{prefix}/{lookup_field}/`
- **功能**: 部分更新资源
- **路径参数**: 
  - `{lookup_field}`: 资源标识符
- **请求体**: 部分字段（可选）
- **响应**: 更新后的资源详情

#### DestroyModelMixin
- **方法**: `DELETE /{prefix}/{lookup_field}/`
- **功能**: 软删除资源（设置 `is_deleted=True`）
- **路径参数**: 
  - `{lookup_field}`: 资源标识符
- **响应**: 成功状态（204 No Content）

#### DestroyManyMixin
- **方法**: `DELETE /{prefix}/batch/`
- **功能**: 批量软删除资源，事务内逐条调用 `perform_destroy`
- **请求体**: `{"ids": [1, 2]}`，也支持查询参数 `?ids=1,2`
- **响应**: 成功状态（204 No Content）

### GenericAPIView配置

| 属性 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `router` | APIRouter | FastAPI路由实例 | None |
| `prefix` | str | API路径前缀 | None |
| `queryset` | Model | 数据库模型 | None |
| `serializer_class` | BaseModel | 默认序列化器 | None |
| `serializer_create_class` | BaseModel | 创建操作序列化器 | None |
| `serializer_update_class` | BaseModel | 更新操作序列化器 | None |
| `serializer_list_class` | BaseModel | 列表响应序列化器 | None |
| `serializer_retrieve_class` | BaseModel | 详情响应序列化器 | None |
| `lookup_field` | str | 资源查找字段 | "pk" |
| `ordering` | list | 默认排序字段 | None |
| `pagination_class` | class | 分页类 | None |
| `filter_class` | class | 过滤类 | None |
| `permissions` | list | FastAPI 依赖列表，通常用于认证 | [] |
| `permission_classes` | list | 业务权限类，支持对象权限 | [] |
| `select_related` | list | 外键关联查询优化 | [] |
| `prefetch_related` | list | 反向关系/M2M 预取优化 | [] |
| `atomic_actions` | bool | 写操作是否自动包裹事务 | True |
| `loop_uuid_field` | str | UUID字段名 | None |

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

- `detail=True` 注册为 `/{prefix}/{lookup_field}/toggle-active/`
- `detail=False` 注册为 `/{prefix}/toggle-active/`
- 如果 action 方法声明 `data: SomePydanticModel`，FastAPI 会自动生成请求体和 OpenAPI 文档

### 自定义过滤

```python
from fast_generic_api.core.filter import FilterSet
from models import User

class UserFilter(FilterSet):
    model = User
    exclude_fields = {"offset", "limit", "page", "page_size"}

    # 声明式过滤字段会自动进入 OpenAPI 查询参数
    username__icontains: str | None = None
    is_active: bool | None = None
    
    # 旧版自定义回调仍兼容
    filters = {
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }

# 在视图中使用
class UserViewSet(...):
    filter_class = UserFilter
```

### ModelSerializer 自动生成

```python
from fast_generic_api.core.serializers import ModelSerializer
from models import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active")
        read_only_fields = ("id",)
```

`ModelSerializer` 会从 Tortoise 模型 `_meta.fields_map` 自动推导 Pydantic 字段，并提供 `create()` / `update(instance)` 帮助方法。复杂嵌套关系建议先作为只读输出处理，写入逻辑可在 `perform_create` / `perform_update` 中显式实现。

### 字段级序列化控制

```python
from fast_generic_api.core.schemas import AutoSchemas

class UserListSerializer(AutoSchemas):
    id: int
    username: str
    email: str
    is_active: bool

    class Meta:
        fields = ("id", "username")
```

`AutoSchemas` 支持 `Meta.fields` 白名单和 `Meta.exclude` 黑名单，用于按 action 输出不同字段。常见配置：

```python
class UserViewSet(...):
    serializer_class = UserDetailSerializer
    serializer_list_class = UserListSerializer
    serializer_create_class = UserCreateSerializer
    serializer_update_class = UserUpdateSerializer
```

### 自定义分页

```python
from fast_generic_api.core.pagination import LimitOffsetPagination

class CustomPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 500

# 在视图中使用
class UserViewSet(...):
    pagination_class = CustomPagination
```

### 权限控制

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fast_generic_api.core.exceptions import HTTPPermissionException
from fast_generic_api.core.permissions import BasePermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    # 验证token逻辑
    if not is_valid_token(token):
        raise HTTPPermissionException
    return user

class IsOwner(BasePermission):
    async def has_object_permission(self, request, obj) -> bool:
        return obj.owner_id == request.user.id

# 在视图中使用
class UserViewSet(...):
    permissions = [Depends(get_current_active_user)]  # FastAPI 认证依赖
    permission_classes = [IsOwner]                   # 业务/对象权限
```

### 事务说明

写操作默认包裹在 `backend.in_transaction()` 中，包括：

- `create` / `update` / `partial_update` / `destroy`
- `create_many` / `update_many` / `destroy_many`

批量操作中任意一条失败会整体回滚。若你的 action 或业务代码自行管理事务，可在 ViewSet 上关闭自动事务：

```python
class UserViewSet(...):
    atomic_actions = False
```

### 多 ORM Backend（Tortoise / SQLAlchemy）

ViewSet 通过 `backend` 访问数据库，默认是 Tortoise：

```python
from fast_generic_api.backends import tortoise_backend

class ItemViewSet(...):
    backend = tortoise_backend  # 默认值，可省略
```

切换到 SQLAlchemy 2.x async：

```bash
pip install "fast_generic_api[sqlalchemy]"
# 或
pip install "sqlalchemy[asyncio]>=2.0" aiosqlite
```

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from fast_generic_api.backends import SQLAlchemyBackend
from fast_generic_api.generics import CustomViewSet

engine = create_async_engine("sqlite+aiosqlite:///./app.db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def sa_backend():
    # 简化示例：生产中建议在依赖里管理 session 生命周期
    session = SessionLocal()
    return SQLAlchemyBackend(session)

class ItemViewSet(CustomViewSet):
    queryset = SAItem
    lookup_field = "id"
    backend_provider = sa_backend  # 每请求注入 backend
```

- 测试示例：`tests/test_sqlalchemy_backend.py`
- FilterSet 优先走 `backend.filter`，旧版 Tortoise `qs.filter(...)` 回调仍兼容
- OpenAPI 默认使用统一信封 `Envelope[T]`（`envelope_response=False` 可关）
- 删除：模型有 `is_deleted` 则软删，否则物理删除

### 列表排序（白名单）

```python
class ItemViewSet(...):
    ordering = ["-created_at"]           # 默认排序
    ordering_fields = ["id", "name", "created_at"]  # ?ordering= 允许的字段
```

- 请求：`GET /api/items/?ordering=-name,id`
- 非法字段 → HTTP 400，业务码 `40000`

### 搜索

```python
class ItemViewSet(...):
    search_fields = ["name", "description"]
```

- 请求：`GET /api/items/?search=apple`（对 `search_fields` 做 OR `icontains`）

### 强制分页 / 批量上限 / 节流

```python
class ItemViewSet(...):
    force_pagination = True   # 未设 pagination_class 时回退 LimitOffset
    batch_max_size = 100
    throttle_classes = []     # 可选：AnonRateThrottle 等
```

### 错误码 / 钩子 / 迁移

- [docs/ERROR_CODES.md](docs/ERROR_CODES.md)
- [docs/HOOKS.md](docs/HOOKS.md)
- [docs/MIGRATION.md](docs/MIGRATION.md)
- [CHANGELOG.md](CHANGELOG.md)
- [ROADMAP.md](ROADMAP.md)

### 版本

- **当前：1.0.0**（公开 API 冻结，破坏性变更走 major）

推荐在多表写入时重写 `perform_create` / `perform_update`，而不是绕过 mixin：

```python
class ComboServiceViewSet(...):
    async def perform_create(self, data):
        payload = self.serialize_input_data(data)
        items = payload.pop("items", [])
        combo = await self.backend.create(self.queryset, **payload)
        for item in items:
            await ComboItem.create(combo=combo, **item)
        return combo
```

### 迁移指南

从旧版升级时需要注意：

1. CRUD 路由已采用 RESTful 形式：`GET/POST /{prefix}/`、`GET/PUT/PATCH/DELETE /{prefix}/{lookup}/`。
2. 推荐把列表和详情输出拆成 `serializer_list_class` / `serializer_retrieve_class`，减少列表接口字段量。
3. 推荐把旧版 `filters = {...}` 逐步迁移为声明式字段（旧写法仍兼容）。
4. 写操作默认开启事务；若旧代码中已经手动包裹事务，检查是否需要设置 `atomic_actions = False`。
5. 需要跨 ORM 扩展时，实现 `BaseBackend` 并在 ViewSet 上替换 `backend`。

## 📦 依赖

- **FastAPI** - Web框架
- **Tortoise ORM** - 异步ORM
- **Pydantic** - 数据验证和序列化

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进这个项目！

### 贡献流程

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详情请查看 [LICENSE](LICENSE) 文件

## 💖 致谢

- 感谢 [FastAPI](https://fastapi.tiangolo.com/) 提供优秀的Web框架
- 感谢 [Django REST Framework](https://www.django-rest-framework.org/) 提供设计灵感
- 感谢所有使用和支持这个项目的开发者！

> 🚀 **开始使用**：按照快速开始指南，5分钟内即可构建强大的API服务！