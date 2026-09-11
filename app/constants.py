"""
常量
"""

import os

from dotenv import load_dotenv


load_dotenv()

# 默认的 npm 包仓库
DEFAULT_NPM_REGISTRY: str = "https://registry.npmjs.org/"
NPM_REGISTRY: str = os.getenv("NPM_REGISTRY") or DEFAULT_NPM_REGISTRY

# opencode server 监听的主机名
DEFAULT_OPENCODE_SERVER_HOSTNAME: str = "127.0.0.1"
OPENCODE_SERVER_HOSTNAME: str = os.getenv("OPENCODE_SERVER_HOSTNAME") or DEFAULT_OPENCODE_SERVER_HOSTNAME

# opencode server 监听的端口号
DEFAULT_OPENCODE_SERVER_PORT: int = 4096
OPENCODE_SERVER_PORT: int = int(
	os.getenv("OPENCODE_SERVER_PORT") or DEFAULT_OPENCODE_SERVER_PORT
)
