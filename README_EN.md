# dummy_model

[中文](README.md)

A honeypot that fights back against API token thieves. Fully emulates the Anthropic Claude Messages API protocol while serving randomly generated token streams — attackers waste resources and get nothing of value.


## Quick Start

### Docker (recommended)

```bash
docker compose up -d
```

### Run directly

```bash
pip install -r requirements.txt
python -m app.main
```

The server listens on `http://0.0.0.0:8000` by default.

## Configuration

Adjust via environment variables or `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DUMMY_HOST` | `0.0.0.0` | Listen address |
| `DUMMY_PORT` | `8000` | Listen port |
| `DUMMY_API_KEY` | (empty) | API key validation — leave empty to accept any key (honeypot open mode) |
| `DUMMY_DELAY_MIN` | `0.01` | Min delay between streaming deltas (seconds) |
| `DUMMY_DELAY_MAX` | `0.05` | Max delay between streaming deltas (seconds) |
| `DUMMY_LOG_LEVEL` | `info` | Log level |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/messages` | POST | Claude Messages API, supports streaming and non-streaming |
| `/v1/models` | GET | Model list |
| `/health` | GET | Health check |

## Usage Examples

### Non-streaming request

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

### Streaming request

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

### Extended thinking

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

### Interactive chat

```bash
python chat.py                 # default: localhost:8000
python chat.py http://host:port  # custom address
```

Type `quit` to exit, `clear` to reset conversation history.

## Protocol Compatibility

Fully compatible with the Anthropic Claude Messages API protocol, including:

- Request format (model, messages, system, max_tokens, temperature, stream, thinking, etc.)
- SSE streaming event sequence (message_start → content_block_start → content_block_delta → content_block_stop → message_delta → message_stop)
- Thinking mode (thinking_delta + signature_delta)
- Non-streaming complete responses
- Token usage statistics (input_tokens, output_tokens, cache fields)

Any client compatible with the Anthropic SDK or API spec can connect directly — no code changes required.

## Project Structure

```
dummy_model/
├── app/
│   ├── main.py        # FastAPI application
│   ├── models.py      # Claude API request/response models
│   ├── generator.py   # Random token generator + toxic payloads
│   └── config.py      # Configuration management
├── chat.py            # Interactive chat script
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

MIT
