import asyncio
import os
import json
from contextlib import asynccontextmanager
from enum import Enum
from typing import AsyncGenerator, List, Optional

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
) -> str:
    """
    Downloads transcripts or summarizes content from a YouTube URL.

    :param url: The URL of the YouTube video, playlist, or channel.
    :param target_langs: Optional list of preferred language codes for captions (e.g., ['en', 'zh-CN']).
    """
    try:
        print(f"正在处理 URL: {url}")
        yt = YouTube(url)
        
        # 调用重构后的函数获取元数据和字幕内容
        metadata_payload = dl_caption_byId(yt, target_langs)
        
        if metadata_payload:
            # 确保 'downloads' 目录存在
            store_path = 'downloads'
            os.makedirs(store_path, exist_ok=True)
            
            # 保存为 JSON 文件
            file_path = os.path.join(store_path, f"{metadata_payload['video_id']}_metadata.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_payload, f, ensure_ascii=False, indent=4)
            
            success_msg = f"成功处理视频 '{metadata_payload['title']}'。元数据和字幕内容已保存到: {file_path}"
            print(success_msg)
            return success_msg
        else:
            error_msg = f"无法为 URL {url} 获取字幕和元数据。"
            print(error_msg)
            return error_msg

    except Exception as e:
        # 错误处理
        error_msg = f"处理 URL {url} 时发生错误: {e}"
        print(error_msg)
        return error_msg

# 5. 简化服务器启动入口
# FastMCP 极大地简化了服务器的启动过程。
if __name__ == "__main__":
    mcp.run()
