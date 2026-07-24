import pytest
import pytest_asyncio
from fastapi import APIRouter
from pydantic import BaseModel

pytest.importorskip("sqlalchemy")

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fast_generic_api.backends import SQLAlchemyBackend
from fast_generic_api.core.filter import FilterSet
from fast_generic_api.core.pagination import LimitOffsetPagination
from fast_generic_api.generics import CustomViewSet
from fast_generic_api.mixins import CreateManyMixin, DestroyManyMixin, UpdateManyMixin
from tests.conftest import build_client


class Base(DeclarativeBase):
    pass


class SAItem(Base):
    __tablename__ = "sa_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class SAItemSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None = None
    is_active: bool
    is_deleted: bool


class SAItemCreateSerializer(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class SAItemUpdateSerializer(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SAItemListSerializer(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str


class SAItemFilter(FilterSet):
    model = SAItem
    name__icontains: str | None = None
    is_active: bool | None = None


@pytest_asyncio.fixture
async def sa_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def make_sa_viewset(session: AsyncSession, api_router: APIRouter, *, prefix: str = "/sa-items"):
    backend = SQLAlchemyBackend(session)
    return type(
        "SAItemViewSet",
        (CreateManyMixin, UpdateManyMixin, DestroyManyMixin, CustomViewSet),
        {
            "router": api_router,
            "prefix": prefix,
            "queryset": SAItem,
            "lookup_field": "id",
            "backend": backend,
            "filter_class": SAItemFilter,
            "ordering": ["id"],
            "pagination_class": LimitOffsetPagination,
            "serializer_class": SAItemSerializer,
            "serializer_create_class": SAItemCreateSerializer,
            "serializer_update_class": SAItemUpdateSerializer,
            "serializer_list_class": SAItemListSerializer,
        },
    )


@pytest.mark.asyncio
async def test_sqlalchemy_crud_filter_batch_flow(sa_session):
    viewset = make_sa_viewset(sa_session, APIRouter())
    async with await build_client(viewset) as client:
        create_response = await client.post(
            "/sa-items/",
            json={"name": "Alpha", "description": "first"},
        )
        assert create_response.status_code == 201
        item_id = create_response.json()["data"]["id"]

        await client.post("/sa-items/", json={"name": "Beta", "description": "second", "is_active": True})
        await client.post("/sa-items/", json={"name": "Gamma", "description": "third", "is_active": False})

        list_response = await client.get("/sa-items/?name__icontains=a&is_active=true&limit=1&offset=0")
        assert list_response.status_code == 200
        payload = list_response.json()["data"]
        assert payload["total"] == 2
        assert payload["results"][0]["name"] in {"Alpha", "Beta"}

        update_response = await client.patch(
            f"/sa-items/{item_id}/",
            json={"description": "patched"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["description"] == "patched"

        batch_create = await client.post(
            "/sa-items/batch/",
            json={"items": [{"name": "One"}, {"name": "Two"}]},
        )
        assert batch_create.status_code == 201
        batch_ids = [row["id"] for row in batch_create.json()["data"]]

        batch_delete = await client.request(
            "DELETE",
            "/sa-items/batch/",
            json={"ids": batch_ids},
        )
        assert batch_delete.status_code == 204

        delete_response = await client.delete(f"/sa-items/{item_id}/")
        assert delete_response.status_code == 204

        missing = await client.get(f"/sa-items/{item_id}/")
        assert missing.status_code == 404
