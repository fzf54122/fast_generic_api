# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:42
# @Author  : fzf
# @FileName: generics.py
# @Software: PyCharm
import inspect
from typing import Any, List, Optional, Type

from fastapi import APIRouter, Depends, Request

from fast_generic_api import mixins
from fast_generic_api.backends import BaseBackend, tortoise_backend
from fast_generic_api.core.exceptions import HTTPException, HTTPPermissionException
from fast_generic_api.core.response import envelope_model


async def get_object_or_404(backend: BaseBackend, queryset, **filter_kwargs):
    obj = await backend.first(backend.filter(queryset, **filter_kwargs))
    if not obj:
        raise HTTPException
    return obj


class GenericAPIView:
    """所有 ViewSet 的基类。

    通过 ``__init_subclass__`` 在类定义时自动把 CRUD 方法注册成路由。
    每个 endpoint 都是一个闭包工厂：FastAPI 请求进来后通过 ``Depends`` 注入
    一个**全新**的 ViewSet 实例，避免共享实例导致的并发数据串流。
    """

    prefix: Optional[str] = None
    router: Optional[APIRouter] = None
    loop_uuid_field: Optional[str] = None
    permissions: list = []  # FastAPI 依赖列表，作用于本 ViewSet 的所有路由

    queryset: Any = None  # 模型类（或自定义 queryset）
    action: Optional[str] = None

    pagination_class = None
    filter_class = None

    # ORM 适配后端，默认 Tortoise
    backend: BaseBackend = tortoise_backend
    # 可选：每请求工厂 ``async def provider() -> BaseBackend`` 或同步 callable。
    # 适合 SQLAlchemy 绑定当前 AsyncSession；返回值会写入 view.backend。
    backend_provider = None

    # OpenAPI：是否用统一信封 Envelope[T] 作为 response_model（默认开启）
    envelope_response: bool = True

    serializer_class = None
    serializer_create_class = None
    serializer_update_class = None
    serializer_list_class = None
    serializer_retrieve_class = None

    # 关联查询优化（解决 N+1）
    select_related: list = []
    prefetch_related: list = []

    # 业务权限类（区别于 permissions 的认证依赖）
    permission_classes: list = []

    lookup_field: str = "pk"
    lookup_url_kwarg: Optional[str] = None

    # 写操作默认开启事务
    atomic_actions: bool = True

    # 批量操作上限（Create/Update/Destroy Many）
    batch_max_size: int = 100

    # 列表默认排序；查询参数 ?ordering= 仅允许 ordering_fields 中的字段
    ordering: list = []
    ordering_fields: list | None = None  # None → 默认用 ordering 的字段名作白名单
    ordering_query_param: str = "ordering"

    # ----------------------------------------------------------------------
    # 路由自动注册
    # ----------------------------------------------------------------------
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.router or not cls.prefix:
            return

        method_map = {
            "list": ("GET", False),
            "create": ("POST", False),
            "retrieve": ("GET", True),
            "update": ("PUT", True),
            "partial_update": ("PATCH", True),
            "destroy": ("DELETE", True),
        }

        # 路由顺序很重要：先注册集合路由，再注册自定义 action，最后注册 detail 路由。
        # 否则 /{lookup}/ 会抢先匹配 /batch/ 这类集合 action。
        for method_name, (http_method, needs_lookup) in method_map.items():
            if needs_lookup or not hasattr(cls, method_name):
                continue
            cls._register_route(method_name, http_method, needs_lookup)

        cls._register_custom_actions()

        for method_name, (http_method, needs_lookup) in method_map.items():
            if not needs_lookup or not hasattr(cls, method_name):
                continue
            cls._register_route(method_name, http_method, needs_lookup)

    @classmethod
    def _register_custom_actions(cls):
        """扫描类上所有带 _action_meta 的方法，注册为自定义路由"""
        import inspect as _inspect

        for attr_name in dir(cls):
            if attr_name.startswith("__"):
                continue
            method = getattr(cls, attr_name, None)
            if not callable(method):
                continue
            meta = getattr(method, "_action_meta", None)
            if not meta:
                continue
            cls._register_action_route(attr_name, method, meta)

    @classmethod
    def _register_action_route(cls, method_name, original_method, meta):
        from fast_generic_api.decorator import action as action_decorator  # noqa

        detail = meta["detail"]
        methods = meta["methods"]
        url_path = meta["url_path"] or method_name.replace("_", "-")
        raw_response = meta.get("response_model")
        if raw_response is not None and getattr(cls, "envelope_response", True):
            response_model = envelope_model(raw_response)
        else:
            response_model = raw_response

        lookup_name = cls.lookup_url_kwarg or cls.lookup_field

        async def make_view() -> cls:
            return await cls._create_view_instance()

        async def endpoint(request: Request, **path_params):
            view = path_params.pop("view")
            view.request = request
            view.kwargs = dict(path_params)
            view.action = method_name
            call_kwargs = {}
            if "data" in path_params:
                call_kwargs["data"] = path_params["data"]
            return await original_method(view, request, **call_kwargs)

        # 构造签名：request + (detail 时 lookup) + (有 body 时 data) + view
        params: list[inspect.Parameter] = [
            inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request),
        ]
        if detail:
            params.append(
                inspect.Parameter(lookup_name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Any)
            )
        # 若方法签名声明了 data 参数，则按其类型注入请求体
        sig = inspect.signature(original_method)
        data_param = sig.parameters.get("data")
        if data_param is not None and data_param.annotation is not inspect._empty:
            default = data_param.default if data_param.default is not inspect._empty else inspect._empty
            params.append(
                inspect.Parameter(
                    "data",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=data_param.annotation,
                    default=default,
                )
            )
        params.append(
            inspect.Parameter("view", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=cls, default=Depends(make_view))
        )
        endpoint.__signature__ = inspect.Signature(parameters=params)

        path = f"{cls.prefix.rstrip('/')}/{url_path}/"
        if detail:
            path = f"{cls.prefix.rstrip('/')}/{{{lookup_name}}}/{url_path}/"

        cls.router.add_api_route(
            path,
            endpoint,
            methods=methods,
            name=method_name,
            summary=getattr(original_method, "_summary", method_name.replace("_", " ").title()),
            description=getattr(original_method, "_description", None),
            tags=getattr(original_method, "_tags", None) or [cls.prefix.strip("/")],
            responses=getattr(original_method, "_responses", None),
            response_model=response_model,
            dependencies=cls.permissions,
        )

    @classmethod
    def _register_route(cls, method_name: str, http_method: str, needs_lookup: bool):
        original_method = getattr(cls, method_name)

        # 选择请求体序列化器
        serializer_map = {
            "create": "serializer_create_class",
            "update": "serializer_update_class",
            "partial_update": "serializer_update_class",
        }
        body_serializer = None
        if method_name in serializer_map:
            body_serializer = getattr(cls, serializer_map[method_name], None) or cls.serializer_class

        # 选择响应模型（OpenAPI）：默认包一层统一信封 Envelope[T]
        data_model = None
        many = False
        paginated = False
        if method_name == "list":
            data_model = cls.serializer_list_class or cls.serializer_class
            many = True
            paginated = cls.pagination_class is not None
        elif method_name == "retrieve":
            data_model = cls.serializer_retrieve_class or cls.serializer_class
        elif method_name in ("create", "update", "partial_update"):
            data_model = cls.serializer_class or getattr(cls, serializer_map.get(method_name), None)
        if getattr(cls, "envelope_response", True):
            response_model = envelope_model(data_model, many=many, paginated=paginated)
        else:
            response_model = List[data_model] if (many and data_model is not None) else data_model

        lookup_name = cls.lookup_url_kwarg or cls.lookup_field

        async def make_view() -> cls:
            return await cls._create_view_instance()

        async def endpoint(request: Request, **path_params):
            view = path_params.pop("view")
            view.request = request
            view.kwargs = dict(path_params)  # 路径/body 参数写入实例
            view.action = method_name
            # 按方法签名透传必要参数
            call_kwargs = {}
            if "data" in path_params:
                call_kwargs["data"] = path_params["data"]
            return await original_method(view, request, **call_kwargs)

        # 动态构造签名，让 FastAPI 解析路径参数、请求体并生成 OpenAPI 文档
        # 顺序：无默认值参数在前（request/pk/data），带默认值的 view 放最后
        params: list[inspect.Parameter] = [
            inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request),
        ]
        if needs_lookup:
            params.append(
                inspect.Parameter(lookup_name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Any)
            )
        if body_serializer is not None:
            params.append(
                inspect.Parameter("data", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=body_serializer)
            )
        # 如果是 list 且 filter_class 有 request model，注入查询参数（OpenAPI 可见）
        if method_name in ("list",) and cls.filter_class is not None:
            request_model = getattr(cls.filter_class, "get_request_model", None)
            if request_model:
                rm = request_model()
                if rm is not None:
                    params.append(
                        inspect.Parameter("filter_params", inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                          annotation=rm, default=Depends(rm))
                    )
        params.append(
            inspect.Parameter("view", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=cls, default=Depends(make_view))
        )

        # 直接用新参数列表构造签名，避免保留原 endpoint 的 **path_params
        endpoint.__signature__ = inspect.Signature(parameters=params)

        # RESTful 路径：list/create -> /prefix/，其余 -> /prefix/{lookup}/
        path = cls.prefix.rstrip("/") + "/"
        if needs_lookup:
            path = f"{cls.prefix.rstrip('/')}/{{{lookup_name}}}/"

        cls.router.add_api_route(
            path,
            endpoint,
            methods=[http_method],
            name=method_name,
            summary=getattr(original_method, "_summary", method_name.replace("_", " ").title()),
            description=getattr(original_method, "_description", None),
            tags=getattr(original_method, "_tags", None) or [cls.prefix.strip("/")],
            responses=getattr(original_method, "_responses", None),
            response_model=response_model,
            dependencies=cls.permissions,
        )

    # ----------------------------------------------------------------------
    # 实例状态（每次请求由 Depends 重新创建）
    # ----------------------------------------------------------------------
    def __init__(self, request: Request = None):
        self.request = request
        self.kwargs = {}
        self.action = None
        self.format_kwarg = None

    @classmethod
    async def _create_view_instance(cls):
        """创建 ViewSet 实例；若配置 backend_provider 则注入每请求 backend。"""
        view = cls()
        provider = getattr(cls, "backend_provider", None)
        if provider is not None:
            backend = provider()
            if inspect.isawaitable(backend):
                backend = await backend
            view.backend = backend
        return view

    # ================================
    # queryset / 对象获取
    # ================================
    def get_queryset(self):
        assert self.queryset is not None, (
            f"'{self.__class__.__name__}' 必须提供 queryset 或重写 get_queryset()"
        )
        model = self.queryset
        # Model 类走 backend.get_queryset；已构造的查询对象直接使用
        if isinstance(model, type):
            queryset = self.backend.get_queryset(model)
        else:
            queryset = model
        # 默认过滤软删除记录
        meta = self.backend.get_model_meta(self.backend.resolve_model(queryset))
        if meta is not None and "is_deleted" in getattr(meta, "fields_map", {}):
            queryset = self.backend.filter(queryset, is_deleted=False)
        # 关联查询优化
        if self.select_related:
            queryset = self.backend.select_related(queryset, *self.select_related)
        if self.prefetch_related:
            queryset = self.backend.prefetch_related(queryset, *self.prefetch_related)
        return queryset

    def filter_queryset(self, queryset):
        if self.filter_class is not None:
            queryset = self.filter_class(
                request=self.request,
                queryset=queryset,
                backend=self.backend,
            ).qs()
        return queryset

    async def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            f'视图 {self.__class__.__name__} 需要 URL 参数 "{lookup_url_kwarg}"'
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await get_object_or_404(self.backend, queryset, **filter_kwargs)
        await self.check_object_permissions(obj)
        return obj

    # ================================
    # serializer
    # ================================
    def get_serializer(self, instance, many: bool = False):
        serializer_class = self.get_response_serializer_class()
        if many:
            return [serializer_class.model_validate(obj) for obj in instance]
        return serializer_class.model_validate(instance)

    def get_serializer_class(self):
        """根据 action 返回请求体 Pydantic 类（create/update 使用输入 serializer）。"""
        mapping = {
            "list": self.serializer_list_class,
            "retrieve": self.serializer_retrieve_class,
            "create": self.serializer_create_class,
            "update": self.serializer_update_class,
            "partial_update": self.serializer_update_class,
        }
        return mapping.get(self.action) or self.serializer_class

    def get_response_serializer_class(self):
        """根据 action 返回输出 Pydantic 类，避免把输入 serializer 用于 ORM 实例响应。"""
        mapping = {
            "list": self.serializer_list_class,
            "retrieve": self.serializer_retrieve_class,
        }
        return mapping.get(self.action) or self.serializer_class or self.get_serializer_class()

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    # ================================
    # 分页
    # ================================
    @property
    def paginator(self):
        if not hasattr(self, "_paginator"):
            self._paginator = None if self.pagination_class is None else self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    # ================================
    # 权限
    # ================================
    def get_permissions(self):
        """实例化业务权限类，兼容 permission_classes=[Cls] 与 [Cls()]。"""
        return [perm() if inspect.isclass(perm) else perm for perm in self.permission_classes]

    async def check_permissions(self):
        """请求级权限检查（list/create 前调用）"""
        for perm in self.get_permissions():
            if not await perm.has_permission(self.request):
                raise HTTPPermissionException

    async def check_object_permissions(self, obj):
        """对象级权限检查（retrieve/update/destroy 取到对象后调用）"""
        # 旧的 callable 式 permissions：只兼容真正可调用的二参函数；FastAPI Depends 会在路由层处理
        for perm in self.permissions:
            if not callable(perm):
                continue
            allowed = perm(self.request, obj)
            if inspect.isawaitable(allowed):
                allowed = await allowed
            if not allowed:
                raise HTTPPermissionException
        for perm in self.get_permissions():
            if not await perm.has_object_permission(self.request, obj):
                raise HTTPPermissionException

    def serialize_input_data(self, input_data) -> dict:
        """将输入数据（Pydantic 模型或 dict）转换为 dict"""
        if isinstance(input_data, dict):
            return input_data
        return input_data.model_dump(exclude_unset=True)


# ----------------------------------------------------------------------
# 具体ViewSet组合（与 DRF 命名对齐）
# ----------------------------------------------------------------------
class CreateViewSet(mixins.CreateModelMixin, GenericAPIView):
    pass


class ListViewSet(mixins.ListModelMixin, GenericAPIView):
    pass


class RetrieveViewSet(mixins.RetrieveModelMixin, GenericAPIView):
    pass


class UpdateViewSet(mixins.PartialUpdateModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    pass


class DestroyViewSet(mixins.DestroyModelMixin, GenericAPIView):
    pass


class ListCreateViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
    pass


class RetrieveUpdateViewSet(
    mixins.PartialUpdateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    pass


class RetrieveDestroyViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, GenericAPIView):
    pass


class RetrieveUpdateDestroyViewSet(
    mixins.PartialUpdateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    pass


class CustomViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.PartialUpdateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    pass
