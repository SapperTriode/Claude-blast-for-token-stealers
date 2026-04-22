"""
Claude Messages API 的请求/响应 Pydantic 模型。
严格按照 Anthropic Claude Messages API 协议定义，
确保蜜罐对外提供的接口与真实服务完全一致。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================
# 请求模型
# ============================================================


class ClaudeMessageSource(BaseModel):
    """消息中媒体资源的来源描述（base64 或 URL）"""
    type: str  # "base64" 或 "url"
    media_type: str | None = None  # 如 "image/png", "application/pdf"
    data: Any = None  # base64 编码字符串
    url: str | None = None


class ClaudeMediaMessage(BaseModel):
    """消息内容块，可以是文本、图片、工具调用等多种类型"""
    type: str  # "text", "image", "tool_use", "tool_result", "thinking" 等
    text: str | None = None
    source: ClaudeMessageSource | None = None
    thinking: str | None = None
    signature: str | None = None
    tool_use_id: str | None = None
    name: str | None = None
    input: Any = None
    content: Any = None
    cache_control: Any = None


class ClaudeMessage(BaseModel):
    """单条消息，包含角色和内容"""
    role: Literal["user", "assistant"]
    content: str | list[ClaudeMediaMessage]


class ThinkingConfig(BaseModel):
    """扩展思考配置"""
    type: Literal["enabled", "adaptive"] = "enabled"
    budget_tokens: int | None = None


class ClaudeRequest(BaseModel):
    """Claude Messages API 请求体"""
    model: str
    messages: list[ClaudeMessage] = Field(default_factory=list)
    system: str | list[dict[str, Any]] | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    stream: bool | None = None
    stop_sequences: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: dict[str, Any] | None = None
    thinking: ThinkingConfig | None = None
    metadata: dict[str, Any] | None = None


# ============================================================
# 响应模型（非流式）
# ============================================================


class ClaudeUsage(BaseModel):
    """Token 用量统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class ClaudeTextBlock(BaseModel):
    """文本内容块"""
    type: Literal["text"] = "text"
    text: str


class ClaudeToolUseBlock(BaseModel):
    """工具调用内容块"""
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)


class ClaudeThinkingBlock(BaseModel):
    """思考内容块"""
    type: Literal["thinking"] = "thinking"
    thinking: str
    signature: str = ""


class ClaudeResponse(BaseModel):
    """Claude Messages API 非流式响应体"""
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list[ClaudeTextBlock | ClaudeToolUseBlock | ClaudeThinkingBlock]
    model: str
    stop_reason: Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"] = "end_turn"
    stop_sequence: str | None = None
    usage: ClaudeUsage


# ============================================================
# SSE 流式事件模型
# ============================================================


class MessageStartMessage(BaseModel):
    """message_start 事件中的 message 字段"""
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list = Field(default_factory=list)
    model: str
    stop_reason: None = None
    stop_sequence: None = None
    usage: ClaudeUsage


class MessageStartEvent(BaseModel):
    """SSE 事件: message_start"""
    type: Literal["message_start"] = "message_start"
    message: MessageStartMessage


class TextContentBlock(BaseModel):
    """content_block_start 中的文本块"""
    type: Literal["text"] = "text"
    text: str = ""


class ThinkingContentBlock(BaseModel):
    """content_block_start 中的思考块"""
    type: Literal["thinking"] = "thinking"
    thinking: str = ""


class ContentBlockStartEvent(BaseModel):
    """SSE 事件: content_block_start"""
    type: Literal["content_block_start"] = "content_block_start"
    index: int
    content_block: TextContentBlock | ThinkingContentBlock


class TextDelta(BaseModel):
    """文本增量内容"""
    type: Literal["text_delta"] = "text_delta"
    text: str


class ThinkingDelta(BaseModel):
    """思考增量内容"""
    type: Literal["thinking_delta"] = "thinking_delta"
    thinking: str


class SignatureDelta(BaseModel):
    """签名增量内容"""
    type: Literal["signature_delta"] = "signature_delta"
    signature: str
    delta: str = ""


class ContentBlockDeltaEvent(BaseModel):
    """SSE 事件: content_block_delta"""
    type: Literal["content_block_delta"] = "content_block_delta"
    index: int
    delta: TextDelta | ThinkingDelta | SignatureDelta


class ContentBlockStopEvent(BaseModel):
    """SSE 事件: content_block_stop"""
    type: Literal["content_block_stop"] = "content_block_stop"
    index: int


class DeltaStop(BaseModel):
    """message_delta 中的 stop 信息"""
    stop_reason: str
    stop_sequence: str | None = None


class DeltaUsage(BaseModel):
    """message_delta 中的用量信息（仅含 output_tokens）"""
    output_tokens: int


class MessageDeltaEvent(BaseModel):
    """SSE 事件: message_delta"""
    type: Literal["message_delta"] = "message_delta"
    delta: DeltaStop
    usage: DeltaUsage


class MessageStopEvent(BaseModel):
    """SSE 事件: message_stop"""
    type: Literal["message_stop"] = "message_stop"
