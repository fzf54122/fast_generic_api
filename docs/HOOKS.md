# 可覆盖钩子清单

ViewSet / Mixin 扩展点（按调用顺序）。

## 请求生命周期

| 钩子 | 位置 | 何时调用 |
|------|------|----------|
| `backend_provider` | 类属性 | 每请求创建 view 后注入 `view.backend` |
| `check_permissions` | GenericAPIView | list / create / batch 前 |
| `check_throttles` | GenericAPIView | list / create 前（可选） |
| `get_queryset` | GenericAPIView | 取对象集；适合机构隔离 |
| `filter_queryset` | GenericAPIView | 应用 `filter_class` |
| `apply_search` | BaseMixin | list 时 `?search=` |
| `get_ordering` | BaseMixin | list 时 `?ordering=` |
| `check_object_permissions` | GenericAPIView | retrieve / update / destroy 取到对象后 |
| `get_serializer_class` | GenericAPIView | 输入 serializer |
| `get_response_serializer_class` | GenericAPIView | 输出 serializer |
| `get_serializer` | GenericAPIView | ORM → Pydantic |
| `perform_create` / `perform_update` / `perform_destroy` | Mixin | 实际写库；多表写放这里 |
| `serialize_input_data` | GenericAPIView | body → dict |

## 配置类属性

| 属性 | 说明 |
|------|------|
| `queryset` | 模型类 |
| `backend` / `backend_provider` | ORM 适配 |
| `filter_class` | 声明式过滤 |
| `pagination_class` / `force_pagination` | 分页 |
| `ordering` / `ordering_fields` | 默认排序与白名单 |
| `search_fields` | 搜索字段 |
| `permission_classes` | 业务权限 |
| `permissions` | FastAPI 认证 Depends |
| `throttle_classes` | 节流 |
| `batch_max_size` | 批量上限 |
| `serializer_*_class` | 按 action 切 serializer |
| `select_related` / `prefetch_related` | 关联优化 |
| `atomic_actions` | 写操作事务开关 |
| `envelope_response` | OpenAPI 信封 |

## 请求上下文

```python
def get_queryset(self):
    qs = super().get_queryset()
    institution_id = self.request.headers.get("X-Institution-Id")
    if institution_id:
        self.context["institution_id"] = institution_id
        qs = self.backend.filter(qs, institution_id=institution_id)
    return qs
```

`self.context` 供 `perform_*` 与 action 共享请求级数据。
