# OpenCode Server Reverse Proxy

一个基于 FastAPI 的 OpenCode Server 反向代理服务，自动安装依赖、启动 OpenCode 服务，并统一代理 HTTP、SSE 和 WebSocket 流量。

## 简介

本项目将 [OpenCode](https://opencode.ai) 的本地服务通过反向代理暴露出来。启动时自动完成以下工作：

1. 更新 `apt` 并安装 `curl`
2. 安装 Node.js 20.x
3. 通过 npm 安装 `opencode-ai`
4. 验证 OpenCode 版本
5. 启动 `opencode serve` 子进程
6. 将外部请求（HTTP / SSE / WebSocket）反向代理到本地 OpenCode Server
7. 服务退出时自动清理 OpenCode 子进程

最终对外提供统一的 FastAPI 服务，所有路径均代理至 OpenCode Server。

## 功能特性

- **自动安装**：无需手动准备 Node.js 和 OpenCode 环境。
- **全协议代理**：支持 HTTP REST、SSE 长连接、WebSocket 全双工通信。
- **生命周期管理**：随 FastAPI 应用启动/关闭自动管理 OpenCode 子进程。
- **环境变量配置**：灵活调整 npm 仓库、监听地址和端口。
- **单例配置**：全局配置通过 `pydantic` 数据类管理，类型安全。

## 架构

```
客户端  →  FastAPI (your_hostname:your_port)  →  OpenCode Server (127.0.0.1:4096)
                 │
                 ├── HTTP / SSE / WebSocket 反向代理
                 └── 生命周期内自动安装与启动
```

## 环境要求

- Python 3.10+
- 操作系统：Debian / Ubuntu（依赖 `apt-get`）
- 需要 root 权限（用于安装系统包）
- 可访问互联网（下载 Node.js 与 npm 包）

## 快速开始

假设您已经有了一个 FastAPI 应用项目。

### 克隆项目

```bash
cd path/to/your/project
git submodule add https://github.com/Jerry-Wu-GitHub/opencode-server-reverse-proxy.git opencode_server
git submodule update --remote
```

### 安装依赖

```bash
python -m pip install -r "opencode_server/requirements.txt"
```

### 注册路由

```python
from fastapi import FastAPI
from opencode_server import get_router_and_lifespan

opencode_proxy_router, opencode_proxy_lifespan = get_router_and_lifespan()

app = FastAPI(lifespan=opencode_proxy_lifespan)
app.include_router(opencode_proxy_router, prefix="/opencode")
```

运行您的应用后，访问 `GET /opencode` 就能与 OpenCode 连接。

## 配置

通过环境变量或 `.env` 文件进行配置：

| 环境变量                   | 说明                    | 默认值                        |
| -------------------------- | ----------------------- | ----------------------------- |
| `NPM_REGISTRY`             | npm 包仓库地址          | `https://registry.npmjs.org/` |
| `OPENCODE_SERVER_HOSTNAME` | OpenCode 本地监听主机名 | `127.0.0.1`                   |
| `OPENCODE_SERVER_PORT`     | OpenCode 本地监听端口   | `4096`                        |

以及 OpenCode 本身支持的环境变量，如：

| 环境变量                   | 说明                       |
| -------------------------- | -------------------------- |
| `OPENCODE_INSTALL_DIR`     | OpenCode 的安装位置        |
| `OPENCODE_DATA_DIR`        | OpenCode 的数据存储位置    |
| `OPENCODE_SERVER_USERNAME` | OpenCode Server 的用户名   |
| `OPENCODE_SERVER_PASSWORD` | OpenCode Server 的认证密码 |

## 注意事项

- 安装步骤需要 root 权限，建议在容器或具有 sudo 权限的环境中运行。
- 首次启动会下载 Node.js 和 OpenCode，耗时取决于网络状况。
- OpenCode 子进程随 FastAPI lifespan 退出而终止，若需长期运行请确保进程不被意外杀死。
