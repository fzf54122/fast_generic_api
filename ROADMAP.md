# fast_generic_api 路线图（→ 1.0）

> 当前目标版本：**0.2.0**（可提交、可打 tag）  
> 下一目标：**1.0.0**（生产可用、API 稳定、文档完整）

活文档：`fast_generic_api/example/`（`ItemViewSet`）  
测试：`tests/`（Tortoise + SQLAlchemy）

---

## 0.2.0（已发布：tag `v0.2.0`）

- [x] Backend 抽象：Tortoise 默认 + SQLAlchemy 可选
- [x] `@action` / 按 action 切 serializer / 声明式 FilterSet
- [x] 权限类、分页、批量 mixin、软删
- [x] 统一响应信封 `Envelope` + OpenAPI 对齐
- [x] 写操作事务样板 `_run_atomic`
- [x] destroy：有 `is_deleted` 软删，否则物理删除
- [x] `backend_provider` 每请求注入 backend（SQLAlchemy session 友好）
- [x] 包元数据 / 版本统一为 0.2.0
- [x] 测试覆盖率 ≥ 80%

**0.2 定位**：功能闭环的 **beta 可用** 库，API 仍可能小改。

## 0.3.0（已发布：tag `v0.3.0`）

- [x] `?ordering=` 查询排序 + `ordering_fields` 白名单
- [x] `batch_max_size` 批量上限（默认 100）
- [x] `HTTPBadRequestException`（40000）+ [docs/ERROR_CODES.md](docs/ERROR_CODES.md)
- ⏭️ 可选：`?search=` / `search_fields`（放到 0.4）
---

## 为什么你「没思路」——其实是阶段切换了

0.x 做的是 **「DRF 最小可用子集」**。到 1.0，重点不再是再堆 CRUD，而是：

1. **稳定契约**（OpenAPI、错误码、版本策略）  
2. **生产体验**（DI、观测、限流、鉴权集成）  
3. **扩展生态**（插件点、Admin 友好、代码生成）  
4. **真实业务样板**（不重做 Combo，但要多资源 / 关系 / 机构隔离示范）

下面按 **价值 × 与现有风格契合度** 排优先级。

---

## 1.0 必做（建议全部完成再标 1.0）

### A. API 契约冻结（最高优先）

| 项 | 说明 | 为何 1.0 需要 |
|----|------|----------------|
| 错误码表 | `code` 分段：4xxxx 客户端 / 5xxxx 服务端，文档化 | 前端/网关可依赖 |
| 校验错误信封 | Pydantic `RequestValidationError` → 统一 `Response` | 现在可能仍是 FastAPI 默认 422 |
| OpenAPI 完整 | 列表分页、batch、action 都在 `/docs` 可看对 | 对外库门槛 |
| 兼容策略 | `CHANGELOG` + SemVer；破坏性改动必须 major | 用户敢升级 |
| 依赖下限 | 锁住实测过的 fastapi/tortoise/pydantic 范围 | 可安装、可复现 |

### B. 依赖注入与生命周期（优雅度核心）

| 项 | 说明 |
|----|------|
| `backend_provider` 完善 | 支持 async generator（请求结束 close session） |
| `get_current_user` 约定 | 文档化 `request.user` 如何挂载（中间件 / Depends） |
| 可覆盖钩子清单 | `get_queryset` / `perform_*` / `check_*` / `get_serializer*` 一张表 |
| 上下文对象 | 可选 `view.context`：`user`、`institution_id`、`request_id` |

### C. 查询与序列化补完

| 项 | 说明 |
|----|------|
| ordering 查询参数 | `?ordering=-created_at,name`，白名单防注入 |
| 动态 fields | `?fields=id,name`（可选关闭） |
| search | 简单 `search_fields` + `?search=` |
| ModelSerializer 关系只读 | FK 展开 / nested list 只读；写仍走 `perform_*` |
| SQLAlchemy ModelSerializer | 或明确文档「仅 Tortoise」 |

### D. 安全默认

| 项 | 说明 |
|----|------|
| 批量上限 | `batch_max_size`（默认 100）防打爆 |
| 分页上限已有 | 再加默认强制分页选项 `force_pagination` |
| 过滤器字段白名单 | 声明式以外禁止任意 `__` 穿透 |
| 权限示例 | JWT / OAuth2 完整 example（不是只写 README） |

### E. 质量门槛

| 项 | 说明 |
|----|------|
| 覆盖率 ≥ 90% 核心包 | backends / mixins / generics |
| CI | GitHub Actions：pytest + ruff + 多 Python 3.11/3.12 |
| 类型 | 对外 API 过 pyright basic |
| 示例可启动烟雾 | example 路由注册 + OpenAPI schema 可导出 |

---

## 1.0 强烈建议（体验拉开差距）

### F. 真实业务样板（仍基于 Item 风格，不要硬做 HIS）

在 `example/` 扩到 **2～3 个资源**，展示：

- 父子资源：`Item` + `ItemTag` / `Comment`（FK）
- 机构隔离：`get_queryset` 按 header/user 过滤
- 多表写：`perform_create` 事务内写主表 + 子表
- 自定义 action + 不同 serializer
- 同一套 ViewSet 风格，用户复制即用

### G. 可观测与运维

- 结构化日志钩子：`log_action(view, action, obj, duration_ms)`
- `request_id` 中间件示例
- 慢查询可选计时（backend 包装）
- 健康检查与版本端点示例

### H. 限流 / 节流（轻量）

- 可选 `throttle_classes`（内存 / Redis 后端接口）
- 默认 `AnonRateThrottle` 示意即可，不绑死 Redis

### I. 管理端友好

- `AdminViewSet` 预设：强制鉴权 + 分页 + 审计字段
- 导出 action：`csv` / `xlsx`（可选 extra）

---

## 1.x 可做成生态（1.0 后）

| 方向 | 想法 |
|------|------|
| 代码生成 | `fga gen viewset Item` 从模型生成 ViewSet 草稿 |
| AsyncAPI / SDK | 从 OpenAPI 生成 TS client |
| GraphQL 桥 | 非目标，除非用户刚需 |
| 多租户插件 | `TenantMixin`：header / subdomain |
| 审计日志 mixin | create/update/destroy 写 audit 表 |
| 缓存列表 | `cache_list_seconds` + 键规则 |
| 事件钩子 | `on_created` / `on_updated` 信号式 |
| Admin UI | 不做完整 Admin，可对接 FastAPI Admin / SQLAdmin |

---

## 不建议再堆的（防范围膨胀）

- 完整 RBAC 引擎（交给业务；框架只留 permission 钩子）
- 自研工作流 / 审批流
- 替代 Alembic / Aerich 的迁移系统
- 重度 GraphQL / gRPC 双协议
- 把 SQLAlchemy 与 Tortoise 在 **同一 ViewSet 热切换**（保持 backend 显式配置即可）

---

## 推荐版本节奏

```
0.2.0  ← 现在：功能闭环 + 优雅化小步（提交点）
0.3.0  ← 契约：校验错误信封、错误码表、ordering/search、batch 上限
0.4.0  ← 体验：backend_provider async gen、多资源 example、CI
0.5.0  ← 硬化：类型、覆盖率、安全默认、CHANGELOG
1.0.0  ← 冻结公开 API + 完整 README 迁移指南 + tag
```

每个 minor 只承诺 **可运行 + 文档 + 测试**，避免一次冲 1.0 做不完。

---

## 和你当前风格最契合的「下一刀」清单（若只做 3 件事）

1. **校验错误也走统一信封**（体感立刻专业）  
2. **example 扩成双资源 + 机构隔离**（比空讲 HIS 有用）  
3. **CI + 错误码文档 + CHANGELOG**（封 1.0 的门面）

---

## 成功标准（1.0 Definition of Done）

- 新人 10 分钟内靠 README + example 跑通 CRUD  
- Tortoise / SQLAlchemy 各有一条官方测试路径  
- 破坏性变更有迁移说明  
- `/docs` 与真实 JSON 结构一致  
- 核心模块无「占位作者/假版本」  
- 至少一种生产鉴权示例可复制  
- CI 绿、覆盖率门槛强制  

---

## 一句话

**0.2 = 能当库用；1.0 = 别人敢在生产里依赖你的契约。**  
功能面你已经接近 DRF 子集上限；1.0 的增量主要在 **契约、注入、安全默认、样板与工程化**，不是再造一套 ORM。
