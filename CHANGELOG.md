# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/)。

## 1.0.0

### Added

- `search_fields` + `?search=` 跨字段模糊搜索（Tortoise / SQLAlchemy backend）
- `force_pagination`：未配置分页类时强制 LimitOffset
- `throttle_classes` + `SimpleRateThrottle` / `AnonRateThrottle`（进程内）
- `view.context` 请求上下文
- 双资源 example：`Item` + `Note`，机构隔离 header、多表 `perform_create`
- GitHub Actions CI（Python 3.11 / 3.12）
- 文档：`docs/ERROR_CODES.md`、`docs/HOOKS.md`、`docs/MIGRATION.md`
- `/health` 示例端点

### Changed

- 版本定位为 **稳定 1.0**：公开 API 见 README / HOOKS；破坏性变更走 major

### Notes

- ModelSerializer 仍主要面向 Tortoise；SQLAlchemy 继续用手写 Pydantic
- 嵌套写、动态 `?fields=`、Redis 节流等列为 1.x

## 0.3.0

- `?ordering=` + `ordering_fields` 白名单
- `batch_max_size`（默认 100）
- `HTTPBadRequestException`（40000）与错误码文档

## 0.2.0

- Backend 抽象：Tortoise 默认 + SQLAlchemy 可选
- `@action`、声明式 FilterSet、权限、分页、批量 mixin
- Envelope OpenAPI、`backend_provider`、软/硬删除回退
- 测试套件与 ROADMAP

## 0.1.x

- 初版 CRUD mixin 与自动路由
