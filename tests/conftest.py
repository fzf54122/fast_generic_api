import pytest_asyncio
from fastapi import APIRouter, FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from tortoise.contrib.test import tortoise_test_context

from fast_generic_api.core.exceptions import register_exception_handlers
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination, PageNumberPagination
from fast_generic_api.core.permissions import BasePermission
from fast_generic_api.core.response import Response
from fast_generic_api.decorator import action
from fast_generic_api.generics import CustomViewSet
from tests.models import ItemRecord


class ItemSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None = None
    is_active: bool
    is_deleted: bool


class ItemCreateSerializer(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class ItemUpdateSerializer(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ItemListSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str


class ItemFilter(FilterSet):
    model = ItemRecord
    name__icontains: str | None = None
    is_active: bool | None = None


class DenyAllPermission(BasePermission):
    async def has_permission(self, request: Request) -> bool:
        return False

    async def has_object_permission(self, request: Request, obj) -> bool:
        return False


class AllowOnlyActiveObjectPermission(BasePermission):
    async def has_object_permission(self, request: Request, obj) -> bool:
        return bool(obj.is_active)


class ToggleSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool


@pytest_asyncio.fixture
async def db():
    async with tortoise_test_context(["tests.models"], db_url="sqlite://:memory:") as ctx:
        yield ctx


async def build_client(viewset_class):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(viewset_class.router)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def toggle_active(self, request: Request):
    item = await self.get_object()
    item.is_active = not item.is_active
    await self.backend.save(item)
    return Response(ToggleSerializer.model_validate(item))


toggle_active = action(detail=True, methods=["POST"], response_model=ToggleSerializer)(toggle_active)


def make_item_viewset(api_router: APIRouter, *, prefix: str = "/items", **overrides):
    attrs = {
        "router": api_router,
        "prefix": prefix,
        "queryset": ItemRecord,
        "lookup_field": "id",
        "filter_class": ItemFilter,
        "ordering": ["id"],
        "ordering_fields": ["id", "name", "is_active"],
        "pagination_class": LimitOffsetPagination,
        "serializer_class": ItemSerializer,
        "serializer_create_class": ItemCreateSerializer,
        "serializer_update_class": ItemUpdateSerializer,
        "serializer_list_class": ItemListSerializer,
        "toggle_active": toggle_active,
    }
    attrs.update(overrides)
    return type(f"{prefix.strip('/').replace('-', '_').title()}ViewSet", (CustomViewSet,), attrs)


@pytest_asyncio.fixture
async def client(db):
    viewset = make_item_viewset(APIRouter())
    async with await build_client(viewset) as api_client:
        yield api_client


@pytest_asyncio.fixture
async def page_client(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/page-items",
        pagination_class=PageNumberPagination,
    )
    async with await build_client(viewset) as api_client:
        yield api_client


@pytest_asyncio.fixture
async def denied_client(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/denied-items",
        permission_classes=[DenyAllPermission],
    )
    async with await build_client(viewset) as api_client:
        yield api_client


@pytest_asyncio.fixture
async def object_permission_client(db):
    viewset = make_item_viewset(
        APIRouter(),
        prefix="/object-items",
        permission_classes=[AllowOnlyActiveObjectPermission],
        pagination_class=None,
    )
    async with await build_client(viewset) as api_client:
        yield api_client
