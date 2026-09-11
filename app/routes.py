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

from fastapi import APIRouter, FastAPI
from fastapi_proxy_lib.core.http import ReverseHttpProxy
from fastapi_proxy_lib.core.websocket import ReverseWebSocketProxy
from fastapi_proxy_lib.fastapi.router import RouterHelper

from .config import get_config
from .utils.install import (
    update_and_install_curl, install_nodejs,
    install_opencode, verify_opencode, opencode_server_lifspan
)

config = get_config()


def get_router_and_lifespan(**kwargs) -> tuple[APIRouter, Callable[[FastAPI], AbstractAsyncContextManager]]:
    """
    返回一个 APIRouter 对象用于注册。
    """
    reverse_http_proxy = ReverseHttpProxy(base_url=f"http://{config.opencode_server_address}/")
    reverse_ws_proxy = ReverseWebSocketProxy(base_url=f"ws://{config.opencode_server_address}/")

    helper = RouterHelper()

    # register_router 返回的是 APIRouter
    reverse_http_router = helper.register_router(reverse_http_proxy)
    reverse_ws_router = helper.register_router(reverse_ws_proxy)

    # 聚合路由
    router = APIRouter(**kwargs)
    router.include_router(reverse_http_router)
    router.include_router(reverse_ws_router)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await asyncio.to_thread(update_and_install_curl)
        await asyncio.to_thread(install_nodejs)
        await asyncio.to_thread(install_opencode)
        await asyncio.to_thread(verify_opencode)
        async with opencode_server_lifspan():
            async with helper.get_lifespan()(app):
                yield

    return router, lifespan
