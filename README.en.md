# 🚀 Fast Auto Framework

<div align="center">

**A powerful and elegantly designed FastAPI automation API framework, providing a Django REST Framework-like experience**

[简体中文](README.md) | **English**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tortoise ORM](https://img.shields.io/badge/Tortoise%20ORM-0.20+-orange.svg)](https://tortoise-orm.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[📖 Quick Start](#-quick-start) • [🏗️ Core Features](#-core-features) • [📚 API Reference](#-api-reference) • [🔧 Advanced Configuration](#-advanced-configuration) • [🤝 Contribution](#-contribution)

</div>

## 🌟 Why Choose Fast Auto Framework?

Fast Auto Framework is an automation API framework specifically designed for FastAPI, providing a development experience similar to Django REST Framework, allowing you to quickly build high-quality API services.

<div align="center">

| 🎯 **CRUD Automation** | ⚡ **Rapid Development** | 🛡️ **Type Safety** | 📈 **High Extensibility** |
|:---:|:---:|:---:|:---:|
| Built-in complete CRUD operations | Create APIs in just a few lines of code | Based on Pydantic and Python type annotations | Modular design, easy to extend |

</div>

## ✨ Core Features

### 🔧 CRUD Operations Automation
- **CreateModelMixin** - Create resources
- **ListModelMixin** - List query (supports pagination and filtering)
- **RetrieveModelMixin** - Detail query
- **UpdateModelMixin** - Full update
- **PartialUpdateModelMixin** - Partial update
- **DestroyModelMixin** - Soft delete functionality

### 📦 Generic API Views
- **GenericAPIView** - Unified API view base class
- **Automatic Route Registration** - Automatic route generation based on class attributes
- **Permission Control** - Flexible permission dependency injection
- **Serializer Support** - Support for different serializers for different operations

### 🌐 Response Handling
- **Unified Response Format** - Standardized API response structure
- **Pagination Response** - Built-in pagination information
- **Error Handling** - Unified error response format
- **JSON Serialization** - Automatically handles Pydantic and datetime types

### 🏗️ Advanced Features
- **Filter System** - Flexible query filtering
- **Pagination Support** - LimitOffset pagination mechanism
- **UUID Support** - Custom UUID as primary key
- **Sorting Functionality** - Support for multi-field sorting

## 🛠️ Technology Stack

| Component | Technology Selection | Version Requirements |
|-----------|----------------------|----------------------|
| **Web Framework** | FastAPI | 0.100+ |
| **ORM** | Tortoise ORM | 0.20+ |
| **Serialization** | Pydantic | 2.0+ |
| **Database** | Supports multiple databases | - |
| **Python Version** | Python | 3.11+ |

## 📁 Project Structure

```
fast_auto_framework/
├── __init__.py                 # Package initialization
├── mixins.py                   # CRUD mixin classes
├── generics.py                 # Generic API views
├── core/                       # Core modules
│   ├── __init__.py            # Core module initialization
│   ├── exceptions.py          # Custom exceptions
│   ├── filter.py              # Filter system
│   ├── pagination.py          # Pagination functionality
│   ├── response.py            # Unified response
│   └── status.py              # HTTP status codes
├── example/                    # Example code
│   ├── __init__.py            # Example module initialization
│   └── example.py             # Usage examples
└── README.md                   # Project documentation
```

## 🚀 Quick Start

### ⚡ Install Dependencies

```bash
# Clone the project
git clone git@github.com:fzf54122/fast_generic_api.git
cd fast_auto_framework

# Install dependencies
pip install fastapi tortoise-orm pydantic
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

#### 3. Create API Views

```python
from fastapi import APIRouter
from fast_auto_framework.generics import GenericAPIView
from fast_auto_framework import mixins
from models import User
from serializers import UserInDB, UserCreate, UserUpdate

# Create router
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

#### 4. Start Application

```python
from fastapi import FastAPI
from api.views import router

app = FastAPI(title="Fast Auto Framework Example")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📚 API Reference

### Available Mixin Classes

#### CreateModelMixin
- **Method**: `POST /{prefix}/create/`
- **Functionality**: Create new resources
- **Request Body**: Defined by `serializer_create_class`
- **Response**: Details of the created resource

#### ListModelMixin
- **Method**: `GET /{prefix}/list/`
- **Functionality**: Get resource list
- **Query Parameters**: 
  - `limit`: Number per page (default: 10, max: 1000)
  - `offset`: Offset (default: 0)
  - Other filter fields
- **Response**: Paginated resource list

#### RetrieveModelMixin
- **Method**: `GET /{prefix}/{lookup_field}/`
- **Functionality**: Get single resource details
- **Path Parameters**: 
  - `{lookup_field}`: Resource identifier
- **Response**: Resource details

#### UpdateModelMixin
- **Method**: `PUT /{prefix}/{lookup_field}/`
- **Functionality**: Full update of resource
- **Path Parameters**: 
  - `{lookup_field}`: Resource identifier
- **Request Body**: Defined by `serializer_update_class`
- **Response**: Updated resource details

#### PartialUpdateModelMixin
- **Method**: `PATCH /{prefix}/{lookup_field}/`
- **Functionality**: Partial update of resource
- **Path Parameters**: 
  - `{lookup_field}`: Resource identifier
- **Request Body**: Partial fields (optional)
- **Response**: Updated resource details

#### DestroyModelMixin
- **Method**: `DELETE /{prefix}/{lookup_field}/`
- **Functionality**: Soft delete resource (sets `is_deleted=True`)
- **Path Parameters**: 
  - `{lookup_field}`: Resource identifier
- **Response**: Success status (204 No Content)

### GenericAPIView Configuration

| Attribute | Type | Description | Default Value |
|-----------|------|-------------|---------------|
| `router` | APIRouter | FastAPI router instance | None |
| `prefix` | str | API path prefix | None |
| `queryset` | Model | Database model | None |
| `serializer_class` | BaseModel | Default serializer | None |
| `serializer_create_class` | BaseModel | Serializer for create operations | None |
| `serializer_update_class` | BaseModel | Serializer for update operations | None |
| `lookup_field` | str | Resource lookup field | "pk" |
| `ordering` | list | Default ordering fields | None |
| `pagination_class` | class | Pagination class | None |
| `filter_class` | class | Filter class | None |
| `permissions` | list | Permission dependency list | [] |
| `loop_uuid_field` | str | UUID field name | None |

## 🔧 Advanced Configuration

### Custom Filtering

```python
from fast_auto_framework.core.filter import FilterSet
from models import User

class UserFilter(FilterSet):
    model = User
    exclude_fields = {"offset", "limit"}
    
    # Custom filter methods
    filters = {
        "username": lambda qs, field, value: qs.filter(username__icontains=value),
        "email": lambda qs, field, value: qs.filter(email__icontains=value),
    }

# Use in view
class UserViewSet(...):
    filter_class = UserFilter
```

### Custom Pagination

```python
from fast_auto_framework.core.pagination import LimitOffsetPagination

class CustomPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 500

# Use in view
class UserViewSet(...):
    pagination_class = CustomPagination
```

### Permission Control

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fast_auto_framework.core.exceptions import HTTPPermissionException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    # Token validation logic
    if not is_valid_token(token):
        raise HTTPPermissionException
    return user

# Use in view
class UserViewSet(...):
    permissions = [Depends(get_current_active_user)]
```

## 📦 Dependencies

- **FastAPI** - Web framework
- **Tortoise ORM** - Asynchronous ORM
- **Pydantic** - Data validation and serialization

## 🤝 Contribution

Welcome to submit Issues and Pull Requests to help improve this project!

### Contribution Process

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 💖 Acknowledgments

- Thanks to [FastAPI](https://fastapi.tiangolo.com/) for providing an excellent web framework
- Thanks to [Django REST Framework](https://www.django-rest-framework.org/) for providing design inspiration
- Thanks to all developers who use and support this project!

> 🚀 **Get Started**: Follow the quick start guide to build powerful API services in just 5 minutes!