import asyncio
import os
import json
from contextlib import asynccontextmanager
from enum import Enum
from typing import AsyncGenerator, List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP, Context
import mcp.types as types
from pytubefix import YouTube

from youtube.yt_subtitle_dl import dl_caption_byId


# 1. 定义 Lifespan 管理器 (可选，但推荐)
# FastMCP 支持使用 lifespan 上下文管理器来处理服务器启动和关闭时的逻辑。
@asynccontextmanager
async def lifespan(mcp: Context) -> AsyncGenerator[None, None]:
    """
    服务器生命周期管理。
    """
    # 在这里可以放置服务器启动时需要执行的代码
    # 例如：加载模型、初始化数据库连接等
    print("YouTube Summary MCP Server is starting up...")
    yield
    # 在这里可以放置服务器关闭时需要执行的代码
    print("YouTube Summary MCP Server is shutting down...")

# 2. 实例化 FastMCP
# 使用新的 FastMCP 类来创建服务器实例。
# 它会自动处理依赖项检查。
mcp = FastMCP(
    "youtube-summary-mcp",
    lifespan=lifespan,
)

# 4. 重构工具定义
# 使用 @mcp.tool() 装饰器，将工具的定义和实现合并。
# FastMCP 会根据函数的签名和文档字符串自动生成工具的 schema。
@mcp.tool()
async def summarize_subtitle_id(
    url: str,
    target_langs: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Downloads transcripts from a YouTube URL and returns structured metadata.

    :param url: The URL of the YouTube video.
    :param target_langs: Optional list of preferred language codes for captions.
    :return: A dictionary containing video metadata and transcript, or None if it fails.
    """
    try:
        print(f"正在处理 URL: {url}")
        yt = YouTube(url)
        
        # 调用函数获取元数据和字幕内容
        metadata_payload = dl_caption_byId(yt, target_langs)
        
        if metadata_payload:
            # 成功时直接返回字典
            print(f"成功处理视频 '{metadata_payload['title']}'。")
            return metadata_payload
        else:
            # 失败时返回 None
            error_msg = f"无法为 URL {url} 获取字幕和元数据。"
            print(error_msg)
            return None

    except Exception as e:
        # 异常时也返回 None
        error_msg = f"处理 URL {url} 时发生错误: {e}"
        print(error_msg)
        return None

# 5. 简化服务器启动入口
# FastMCP 极大地简化了服务器的启动过程。
if __name__ == "__main__":
    mcp.run()
