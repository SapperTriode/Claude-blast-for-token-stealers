"""
FastAPI 主应用。
实现 Anthropic Claude Messages API 的蜜罐端点，
对外与真实 API 接口完全一致，内部返回随机生成的内容。
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from . import config, generator, models

logger = logging.getLogger("dummy_model")


# ============================================================
# 生命周期：启动时打印配置
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，启动时记录配置信息"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info(
        "dummy_model 启动 — host=%s port=%d api_key=%s delay=[%.3f, %.3f]",
        config.HOST,
        config.PORT,
        "***" if config.API_KEY else "(无校验)",
        config.DELAY_MIN,
        config.DELAY_MAX,
    )
    yield


app = FastAPI(title="Claude API (dummy)", lifespan=lifespan)


# ============================================================
# 鉴权中间件
# ============================================================


def _check_api_key(x_api_key: str | None) -> None:
    """
    校验 API Key。
    若 config.API_KEY 非空，则请求头中的 x-api-key 必须匹配；
    若 config.API_KEY 为空，则跳过校验（蜜罐开放模式）。
    """
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="invalid x-api-key")


# ============================================================
# SSE 流式响应生成
# ============================================================


async def _stream_response(request: models.ClaudeRequest) -> AsyncIterator[bytes]:
    """
    将 generator 产出的每个事件编码为 SSE 格式的字节流。
    SSE 格式：event: <type>\ndata: <json>\n\n
    每个 delta 之间加入随机延迟，模拟真实模型的生成速度。
    """
    async for event in generator.generate_stream(request):
        event_type = event.get("type", "")
        payload = json.dumps(event, ensure_ascii=False)
        # SSE 标准格式：event 行 + data 行 + 空行
        sse_frame = f"event: {event_type}\ndata: {payload}\n\n"
        yield sse_frame.encode("utf-8")
        # 在 delta 事件之间插入随机延迟
        if "delta" in event_type or "start" in event_type:
            delay = asyncio.get_event_loop().time()
            import random
            delay = random.uniform(config.DELAY_MIN, config.DELAY_MAX)
            await asyncio.sleep(delay)


# ============================================================
# 非流式响应构造
# ============================================================


def _build_non_stream_response(request: models.ClaudeRequest) -> dict:
    """
    构造非流式 Claude Messages API 响应。
    一次性生成全部随机文本并返回完整消息。
    """
    import random
    from .generator import generate_message_id, _estimate_tokens, _generate_toxic_text

    msg_id = generate_message_id()

    # 估算输入 token
    input_text = " ".join(
        m.content if isinstance(m.content, str) else str(m.content)
        for m in request.messages
    )
    input_tokens = max(10, _estimate_tokens(input_text))

    # 生成含有毒载荷的文本
    text = _generate_toxic_text()

    return {
        "id": msg_id,
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": request.model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": _estimate_tokens(text),
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }


# ============================================================
# API 端点
# ============================================================


@app.post("/v1/messages")
async def create_message(
    request: models.ClaudeRequest,
    x_api_key: str | None = Header(default=None),
    anthropic_version: str | None = Header(default=None),
):
    """
    Claude Messages API 主端点。
    接受与 Anthropic Claude API 相同格式的请求，
    根据 stream 字段决定返回流式或非流式响应。
    """
    # 记录请求信息（用于蜜罐监控）
    logger.info(
        "请求: model=%s stream=%s messages=%d",
        request.model,
        request.stream,
        len(request.messages),
    )

    # 鉴权
    _check_api_key(x_api_key)

    # 根据 stream 参数决定响应方式
    if request.stream:
        return StreamingResponse(
            _stream_response(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return _build_non_stream_response(request)


# ============================================================
# 辅助端点：健康检查、兼容性探测
# ============================================================


@app.get("/v1/models")
async def list_models():
    """
    模拟 Claude 模型列表端点。
    返回常见模型名称，使蜜罐在探测时看起来更真实。
    """
    models_list = [
        {"id": "claude-opus-4-20250514", "display_name": "Claude Opus 4"},
        {"id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
        {"id": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet"},
        {"id": "claude-3-5-haiku-20241022", "display_name": "Claude 3.5 Haiku"},
        {"id": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
    ]
    return {"data": models_list}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


# ============================================================
# 启动入口
# ============================================================


def main():
    """启动 uvicorn 服务器"""
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
