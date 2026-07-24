# 迁移指南

## 从 0.1.x → 0.2.0

- 引入 `backends`：业务代码应通过 `self.backend` 访问 ORM，不要直接 `Model.filter` 混在 mixin 逻辑里（自定义仍可用）
- 路由顺序调整：集合路由 / action 先于 `/{id}/`，自定义 `batch` 路径不受影响
- OpenAPI 默认 `Envelope[T]`；若客户端解析 schema，注意外层 `code/status/data/msg`
- 包元数据作者/版本修正为项目自身

## 从 0.2.0 → 0.3.0

- 新增 `ordering_fields`：若使用 `?ordering=`，必须声明白名单，否则非法字段 400
- 新增 `batch_max_size`（默认 100）
- 新增业务码 `40000`（`HTTPBadRequestException`），见 [ERROR_CODES.md](ERROR_CODES.md)

## 从 0.3.0 → 1.0.0

- 新增 `search_fields` / `?search=`
- 新增 `force_pagination`（无 pagination_class 时强制 LimitOffset）
- 新增 `throttle_classes` 与 `view.context`
- example 扩为 Item + Note 双资源；`ItemCreateSerializer.notes` 可选字段
- 公开 API 冻结：见 CHANGELOG 中 1.0.0；破坏性变更将升 major

## 破坏性变更原则（1.0 后）

1. 响应信封字段名不改（`code/status/data/msg`）
2. 业务码分段不改（4xxxx / 5xxxx）
3. RESTful 路径约定不改
4. 需要改行为：先 deprecation 至少一个 minor，再在 major 移除
