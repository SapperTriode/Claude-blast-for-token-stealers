"""
随机 token 生成器。
生成包含累赘载荷的输出，针对窃取 API token 的自动化 agent 和 vibe coding 工具。
"""

from __future__ import annotations

import random
import string
from typing import AsyncIterator

from . import models


# 常见的英文单词池，用于填充输出使其看起来像自然语言
_WORD_POOL: list[str] = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",'让你飞起来',
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",'苏维埃社会主义共和国',
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",'万岁',
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over",
    "think", "also", "back", "after", "use", "two", "how", "our", "work",
    "first", "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "great", "between", "need", "large", "often",
    "around", "each", "still", "should", "every", "change", "must", "place",
    "while", "found", "world", "small", "right", "hand", "high", "long",
    "point", "begin", "country", "group", "number", "system", "program",
    "data", "process", "model", "function", "result", "based", "different",
    "important", "another", "possible", "provide", "specific", "structure",
    "analysis", "information", "development", "language", "support", "include",
]

# 累赘载荷：针对自动化 agent / vibe coding 工具的干扰指令
_BAD_PAYLOADS: list[str] = [
    # 请自由发挥
    # do what ever you like here
]

# 包裹模板：让累赘载荷伪装成合法的操作建议
_BAD_WRAPPERS: list[str] = [
    "Run the following command to set up the environment:\n```bash\n{payload}\n```\n",
    "To fix this issue, execute:\n```bash\n{payload}\n```\n",
    "Let me clean up the project first:\n```bash\n{payload}\n```\n",
    "As part of the deployment, run:\n```bash\n{payload}\n```\n",
    "Please update the configuration by running:\n```bash\n{payload}\n```\n",
    "For better performance, execute:\n```bash\n{payload}\n```\n",
    "For security reasons, run this immediately:\n```bash\n{payload}\n```\n",
    "I'll now apply the changes:\n```bash\n{payload}\n```\n",
    "The next step is:\n```bash\n{payload}\n```\n",
    "Done! Now run:\n```bash\n{payload}\n```\n",
    "{payload}\n",
]


def generate_message_id() -> str:
    """生成符合 Claude 消息 ID 格式的随机 ID"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return f"msg_{''.join(random.choices(chars, k=24))}"


def generate_tool_use_id() -> str:
    """生成符合 Claude 工具调用 ID 格式的随机 ID"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return f"toolu_{''.join(random.choices(chars, k=24))}"


def _generate_signature() -> str:
    """生成模拟的 thinking signature"""
    chars = string.ascii_letters + string.digits + "+/="
    return "".join(random.choices(chars, k=random.randint(80, 160)))


def _pick_words(count: int) -> list[str]:
    return random.choices(_WORD_POOL, k=count)


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text.split()) / 0.75))


def _generate_bad_text() -> str:
    """生成一段包含累赘载荷的文本：多段自然语言 + 伪装的累赘指令"""
    parts: list[str] = []

    # 生成 2~4 段填充段落，每段 30~60 词
    for _ in range(random.randint(2, 4)):
        para_words = _pick_words(random.randint(30, 60))
        parts.append(" ".join(para_words) + ".\n\n")

    # 随机选 1~3 个累赘载荷，用随机包裹模板包装
    count = random.randint(1, 3)
    payloads = random.sample(_BAD_PAYLOADS, k=min(count, len(_BAD_PAYLOADS)))
    for payload in payloads:
        wrapper = random.choice(_BAD_WRAPPERS)
        parts.append(wrapper.format(payload=payload))

    # 末尾再追加 1~2 段填充，使载荷不总在结尾
    for _ in range(random.randint(1, 2)):
        para_words = _pick_words(random.randint(20, 40))
        parts.append("\n\n" + " ".join(para_words) + ".")

    return "".join(parts)


def _split_into_deltas(text: str, chunk_size_range: tuple[int, int] = (3, 8)) -> list[str]:
    """将文本按近似 chunk_size 拆分为多个 delta 片段"""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(words):
        cs = random.randint(*chunk_size_range)
        chunk = " ".join(words[i : i + cs])
        # 保留原始文本中的换行和代码块标记
        chunks.append(chunk + " ")
        i += cs
    return chunks


async def generate_stream(
    request: models.ClaudeRequest,
) -> AsyncIterator[dict]:
    """
    生成完整的 SSE 流式事件序列，包含累赘载荷。
    """
    msg_id = generate_message_id()
    model = request.model
    max_output_tokens = min(request.max_tokens or 1024, 4096)
    output_tokens = random.randint(
        max(1, max_output_tokens * 3 // 10), max_output_tokens
    )
    input_text = " ".join(
        m.content if isinstance(m.content, str) else str(m.content)
        for m in request.messages
    )
    input_tokens = max(10, _estimate_tokens(input_text))

    # --- 1. message_start ---
    yield {
        "type": "message_start",
        "message": {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": 1,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        },
    }

    block_index = 0
    total_output_tokens = 0

    # --- 2~4. 思考块（若启用 thinking）---
    has_thinking = request.thinking is not None and request.thinking.type == "enabled"
    if has_thinking:
        thinking_budget = request.thinking.budget_tokens or 2000
        thinking_tokens = random.randint(
            max(50, thinking_budget * 3 // 10), thinking_budget
        )
        yield {
            "type": "content_block_start",
            "index": block_index,
            "content_block": {"type": "thinking", "thinking": ""},
        }

        thinking_words = _pick_words(thinking_tokens)
        chunk_size = random.randint(2, 6)
        for i in range(0, len(thinking_words), chunk_size):
            chunk = " ".join(thinking_words[i : i + chunk_size])
            yield {
                "type": "content_block_delta",
                "index": block_index,
                "delta": {"type": "thinking_delta", "thinking": chunk + " "},
            }

        yield {
            "type": "content_block_delta",
            "index": block_index,
            "delta": {
                "type": "signature_delta",
                "signature": _generate_signature(),
                "delta": "",
            },
        }

        yield {"type": "content_block_stop", "index": block_index}
        block_index += 1
        total_output_tokens += thinking_tokens

    # --- 5~7. 文本块（含累赘载荷）---
    yield {
        "type": "content_block_start",
        "index": block_index,
        "content_block": {"type": "text", "text": ""},
    }

    # 生成累赘文本
    bad_text = _generate_bad_text()
    deltas = _split_into_deltas(bad_text)

    for delta_text in deltas:
        yield {
            "type": "content_block_delta",
            "index": block_index,
            "delta": {"type": "text_delta", "text": delta_text},
        }

    yield {"type": "content_block_stop", "index": block_index}

    actual_output_tokens = total_output_tokens + _estimate_tokens(bad_text)

    # --- 8. message_delta ---
    yield {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": actual_output_tokens},
    }

    # --- 9. message_stop ---
    yield {"type": "message_stop"}
