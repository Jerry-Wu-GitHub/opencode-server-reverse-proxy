"""
OpenCode Server 反向代理 Router

统一处理三类流量:
  - HTTP REST  (请求-响应, OpenAPI 3.1)
  - SSE        (GET /event 等长连接事件流)
  - WebSocket  (PTY 交互等全双工场景)
"""

import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi_proxy_lib.core.http import ReverseHttpProxy
from fastapi_proxy_lib.core.websocket import ReverseWebSocketProxy
from fastapi_proxy_lib.fastapi.router import RouterHelper

from .config import get_config
from .utils.install import ensure_opencode_running, stop_opencode

config = get_config()


async def require_ready():
    """依赖：确保 OpenCode 就绪；首次请求会触发懒加载（安装 + 启动）。"""
    await ensure_opencode_running()


def get_router_and_lifespan(**kwargs):
    reverse_http_proxy = ReverseHttpProxy(base_url=f"http://{config.opencode_server_address}/")
    reverse_ws_proxy = ReverseWebSocketProxy(base_url=f"ws://{config.opencode_server_address}/")

    helper = RouterHelper()
    reverse_http_router = helper.register_router(reverse_http_proxy)
    reverse_ws_router = helper.register_router(reverse_ws_proxy)

    # 把 require_ready 挂在 router 级别，代理路由全部继承
    router = APIRouter(dependencies=[Depends(require_ready)], **kwargs)
    router.include_router(reverse_http_router)
    router.include_router(reverse_ws_router)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # lifespan 只保留 helper 的资源管理，立即 yield，不阻塞端口监听
        async with helper.get_lifespan()(app):
            yield
        await stop_opencode()

    return router, lifespan
