import asyncio
import subprocess

from ..config import get_config

config = get_config()

# 幂等状态：锁 + 就绪事件 + 子进程句柄
_init_lock: asyncio.Lock | None = None
_ready_event: asyncio.Event | None = None
_opencode_proc: asyncio.subprocess.Process | None = None


def _lock() -> asyncio.Lock:
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


def _ready() -> asyncio.Event:
    global _ready_event
    if _ready_event is None:
        _ready_event = asyncio.Event()
    return _ready_event


def _run(cmd: str, desc: str):
    print(f"{desc}...")
    subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    print(f"{desc} 完成。")


def _do_install():
    """同步执行的安装流程，放到线程里跑，避免阻塞事件循环。"""
    _run("apt-get update && apt-get install -y curl",
         "正在更新 apt 并安装 curl")
    _run(
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && "
        "apt-get install -y nodejs && "
        "apt-get clean && rm -rf /var/lib/apt/lists/*",
        "正在安装 Node.js 20.x",
    )
    _run(f"npm install -g opencode-ai --registry={config.npm_registry}",
         "正在安装 OpenCode")


async def _wait_port(host: str, port: int, timeout: float = 60.0):
    """等待端口真正可连接（避免代理刚起就来请求时连接被拒）。"""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(0.5)
    raise TimeoutError(f"等待 {host}:{port} 就绪超时")


async def ensure_opencode_running():
    """懒加载入口：安装依赖并启动 opencode serve。幂等、并发安全。"""
    global _opencode_proc

    ready = _ready()
    if ready.is_set():
        return

    async with _lock():
        # 双重检查：等锁期间可能已被别的协程完成
        if ready.is_set():
            return

        await asyncio.to_thread(_do_install)

        print(f"启动 OpenCode 服务，监听 {config.opencode_server_address} ...")
        _opencode_proc = await asyncio.create_subprocess_exec(
            "opencode", "serve",
            "--hostname", config.opencode_server_hostname,
            "--port", str(config.opencode_server_port),
        )

        await _wait_port(config.opencode_server_hostname,
                         config.opencode_server_port)

        ready.set()
        print("OpenCode 服务已就绪。")


async def stop_opencode():
    """lifespan 退出时清理子进程。"""
    global _opencode_proc
    if _opencode_proc is not None and _opencode_proc.returncode is None:
        _opencode_proc.terminate()
        try:
            await asyncio.wait_for(_opencode_proc.wait(), timeout=10)
        except asyncio.TimeoutError:
            _opencode_proc.kill()
            await _opencode_proc.wait()
    _opencode_proc = None
