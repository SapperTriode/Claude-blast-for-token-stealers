# Claude Blast for token stealers

[English](README_EN.md)

API 蜜罐服务。完整模拟 Anthropic Claude Messages API 协议，对任何调用者都返回无意义的随机输出，使其无法获取任何有价值的信息。

**核心特性**：输出中混入针对自动化工具的干扰载荷，伪装为正常的操作建议，使自动化客户端在无人监督时执行无意义操作，从而暴露并挫败滥用行为。

> **免责声明**：本项目仅用于防御性安全研究，旨在保护合法 API 资源免受未授权滥用。使用者应确保在自有环境中部署，并遵守当地法律法规。作者不对任何滥用行为承担责任。

## 快速开始

### Docker（推荐）

```bash
docker compose up -d
```

### 直接运行

```bash
pip install -r requirements.txt
python -m app.main
```

服务默认监听 `http://0.0.0.0:8000`。

## 配置

通过环境变量调整，也可在 `docker-compose.yml` 中设置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DUMMY_HOST` | `0.0.0.0` | 监听地址 |
| `DUMMY_PORT` | `8000` | 监听端口 |
| `DUMMY_API_KEY` | （空） | API Key 校验，留空则不校验（蜜罐开放模式） |
| `DUMMY_DELAY_MIN` | `0.01` | 流式 delta 最小延迟（秒） |
| `DUMMY_DELAY_MAX` | `0.05` | 流式 delta 最大延迟（秒） |
| `DUMMY_LOG_LEVEL` | `info` | 日志级别 |
| `DUMMY_MODEL_LIST_FILE` | `model_list` | 模型列表文件路径 |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/messages` | POST | Claude Messages API，支持流式和非流式 |
| `/v1/models` | GET | 模型列表（从文件加载） |
| `/health` | GET | 健康检查 |

## 使用示例

### 非流式请求

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 128,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 流式请求

```bash
curl -N -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 128,
    "stream": true,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 启用扩展思考

```bash
curl -N -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 128,
    "stream": true,
    "thinking": {"type": "enabled", "budget_tokens": 500},
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 交互式对话

```bash
python chat.py                 # 默认连接 localhost:8000
python chat.py http://host:port  # 指定地址
```

对话中输入 `quit` 退出，`clear` 清空历史。

## 协议兼容性

完全兼容 Anthropic Claude Messages API 协议，包括：

- 请求格式（model, messages, system, max_tokens, temperature, stream, thinking 等）
- SSE 流式事件序列（message_start → content_block_start → content_block_delta → content_block_stop → message_delta → message_stop）
- thinking 模式（thinking_delta + signature_delta）
- 非流式完整响应
- Token 用量统计（input_tokens, output_tokens, cache 字段）

任何兼容 Anthropic SDK 或 API 规范的客户端均可直接对接，无需修改代码。

## 项目结构

```
dummy_model/
├── app/
│   ├── main.py        # FastAPI 主应用
│   ├── models.py      # Claude API 请求/响应模型
│   ├── generator.py   # 随机 token 生成器 + 干扰载荷
│   └── config.py      # 配置管理
├── chat.py            # 交互式对话脚本
├── model_list         # 模型名称列表
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

MIT
