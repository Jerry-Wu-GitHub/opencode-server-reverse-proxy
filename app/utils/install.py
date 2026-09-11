import asyncio
from contextlib import asynccontextmanager
import subprocess
import os

from ..config import get_config


config = get_config()


def update_and_install_curl():
    """更新 apt 并安装 curl"""
    cmd = "apt-get update && apt-get install -y curl"
    print("正在更新 apt 并安装 curl...")
    subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    print("curl 安装完成。")


def install_nodejs():
    """安装 Node.js 20.x"""
    cmd = (
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && "
        "apt-get install -y nodejs && "
        "apt-get clean && rm -rf /var/lib/apt/lists/*"
    )
    print("正在安装 Node.js 20.x...")
    subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    print("Node.js 安装完成。")


def install_opencode():
    """通过 npm 安装 OpenCode（使用淘宝镜像加速）"""
    cmd = f"npm install -g opencode-ai --registry={config.npm_registry}"
    print("正在安装 OpenCode...")
    subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    print("OpenCode 安装完成。")


def verify_opencode():
    """验证 OpenCode 安装，返回版本号"""
    print("正在验证 OpenCode 版本...")
    result = subprocess.run(
        "opencode --version",
        shell=True, capture_output=True, text=True,
    )
    version = result.stdout.strip()
    print(f"OpenCode 版本: {version}")
    return version


@asynccontextmanager
async def opencode_server_lifspan():
    """启动 OpenCode 远程服务子进程，随 lifespan 退出自动清理。"""
    print(f"启动 OpenCode 服务，监听 {config.opencode_server_address} ...")

    # 异步启动独立子进程，立即返回，不阻塞
    proc = await asyncio.create_subprocess_exec(
        "opencode", "serve",
        "--hostname", config.opencode_server_hostname,
        "--port", str(config.opencode_server_port),
    )

    try:
        yield
    finally:
        # 优雅关闭子进程
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
