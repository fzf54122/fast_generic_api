# fast_generic_api 路线图

> **1.0.0 已发布**（tag `v1.0.0`）  
> 公开 API 冻结；后续破坏性变更走 major。

活文档：`fast_generic_api/example/`（`Item` + `Note`）  
测试：`tests/`（Tortoise + SQLAlchemy）  
变更记录：[CHANGELOG.md](CHANGELOG.md)

---

## 已发布

| 版本 | 摘要 |
|------|------|
| 0.2.0 | Backend 抽象、action/filter/权限/分页/batch、Envelope、测试 |
| 0.3.0 | ordering 白名单、batch_max_size、错误码文档 |
| 1.0.0 | search、force_pagination、throttle、双资源 example、CI、HOOKS/MIGRATION、API 冻结 |

---

## 1.0 Definition of Done（已满足）

- [x] README + example 可跑通 CRUD
- [x] Tortoise / SQLAlchemy 测试路径
- [x] 迁移说明（docs/MIGRATION.md）
- [x] `/docs` 信封与真实 JSON 对齐
- [x] 无占位作者/假版本
- [x] 机构隔离 + 多表写入样板
- [x] CI（GitHub Actions）
- [x] 覆盖率门槛（CI `--cov-fail-under=80`）

---

## 1.x 可选方向（不阻塞 1.0）

| 方向 | 说明 |
|------|------|
| `?fields=` 动态裁剪 | 输出字段白名单 |
| ModelSerializer 嵌套只读 / SQLAlchemy 版 | 序列化增强 |
| `backend_provider` async generator 生命周期 | session 自动 close |
| Redis 节流后端 | 替换进程内 SimpleRateThrottle |
| 审计 / 多租户 mixin | 插件式 |
| 代码生成 CLI | `fga gen viewset` |
| JWT 完整 example | 生产鉴权样板加厚 |

---

## 不建议再堆

- 完整 RBAC / 工作流 / 自研迁移 / GraphQL 双协议

---

## 一句话

**1.0 = 契约稳定、双 ORM、有样板与 CI，别人敢在业务里依赖。**  
1.x 做体验与生态，不再改信封/路径/业务码分段。
