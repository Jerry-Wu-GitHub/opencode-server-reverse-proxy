"""
配置
"""

from pydantic import Field
from pydantic.dataclasses import dataclass

from .constants import (
    NPM_REGISTRY,
    OPENCODE_SERVER_HOSTNAME,
    OPENCODE_SERVER_PORT,
)


@dataclass(slots=True)
class Config:
    """
    全局配置

    单例模式
    """

    npm_registry: str = Field(
        description="下载 npm 包的仓库",
        default=NPM_REGISTRY,
    )

    opencode_server_hostname: str = Field(
        description="OpenCode 本地运行的监听主机名。",
        default=OPENCODE_SERVER_HOSTNAME,
    )

    opencode_server_port: int = Field(
        description="OpenCode 本地运行的监听端口。",
        default=OPENCODE_SERVER_PORT,
        ge=0,
        le=65535,
    )

    @property
    def opencode_server_address(self):
        """
        OpenCode 本地运行的监听 Socket
        """
        return f"{self.opencode_server_hostname}:{self.opencode_server_port}"



# 模块级唯一实例
_config: Config = Config()


def get_config() -> Config:
    """获取全局配置单例"""
    return _config
