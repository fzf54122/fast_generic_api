# 错误码约定

响应统一信封：

```json
{
  "code": 40000,
  "status": "error",
  "data": null,
  "msg": "Bad request"
}
```

- **HTTP `status_code`**：传输层状态（400 / 403 / 404 / 422 / 500）
- **业务 `code`**：客户端可分支处理的业务码（与 HTTP 分离）

## 分段

| 段 | 含义 |
|----|------|
| 2xxxx | 成功（当前成功统一 `code=200`） |
| 4xxxx | 客户端错误 |
| 5xxxx | 服务端错误 |

## 已定义业务码

| code | HTTP | 异常 / 场景 | 说明 |
|------|------|-------------|------|
| 200 | 2xx | 成功 | 业务成功；HTTP 可能是 200/201/204 |
| 40000 | 400 | `HTTPBadRequestException` | 非法 ordering、batch 超限等业务校验 |
| 40300 | 403 | `HTTPPermissionException` | 权限不足 |
| 40400 | 404 | `HTTPException` | 资源不存在 |
| 42200 | 422 | `RequestValidationError` | Pydantic 请求体/查询参数校验失败；`data` 为错误列表 |
| 50000 | 500 | `FastAutoException` 基类 | 未分类服务端错误 |

## 使用方式

```python
from fast_generic_api.core.exceptions import HTTPBadRequestException

raise HTTPBadRequestException("Batch size 200 exceeds batch_max_size=100")
# → HTTP 400, body.code == 40000, body.msg == "..."
```

可自定义 detail / code：

```python
raise HTTPBadRequestException("too many", code=40001)
```

## 客户端建议

1. 先看 HTTP status 做传输层处理  
2. 再看 `code` 做业务分支  
3. `42200` 时读 `data`（字段级错误）  
4. 未知 4xxxx / 5xxxx 按通用失败处理，勿硬编码未文档化码  
