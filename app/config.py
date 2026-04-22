"""
蜜罐服务配置。
集中管理可调参数，方便通过环境变量或 .env 文件调整。
"""

from __future__ import annotations

import os

# 服务监听地址和端口
HOST: str = os.getenv("DUMMY_HOST", "0.0.0.0")
PORT: int = int(os.getenv("DUMMY_PORT", "8000"))

# 日志级别
LOG_LEVEL: str = os.getenv("DUMMY_LOG_LEVEL", "info")

# API 鉴权：若设置则要求请求头 x-api-key 匹配此值；
# 留空则不校验（方便蜜罐开放吸引攻击者）
API_KEY: str = os.getenv("DUMMY_API_KEY", "")

# 每个 delta 之间的最小/最大延迟（秒），
# 模拟真实模型的生成延迟
DELAY_MIN: float = float(os.getenv("DUMMY_DELAY_MIN", "0.01"))
DELAY_MAX: float = float(os.getenv("DUMMY_DELAY_MAX", "0.05"))

# 模型列表文件路径，每行一个模型名称
MODEL_LIST_FILE: str = os.getenv(
    "DUMMY_MODEL_LIST_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "model_list"),
)
