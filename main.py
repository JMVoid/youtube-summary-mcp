import asyncio
import os
import json
import logging
from contextlib import asynccontextmanager
from enum import Enum
from typing import AsyncGenerator, Optional, Dict, Any

from fastmcp import FastMCP, Context
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
    logging.info("YouTube Summary MCP Server is starting up...")
    yield
    # 在这里可以放置服务器关闭时需要执行的代码
    logging.info("YouTube Summary MCP Server is shutting down...")

# 2. 实例化 FastMCP
# 使用新的 FastMCP 类来创建服务器实例。
# 它会自动处理依赖项检查。
mcp = FastMCP(
    "youtube-summary-mcp",
    lifespan=lifespan,
)

logging.basicConfig(level=logging.INFO)

# 4. 重构工具定义
# 使用 @mcp.tool() 装饰器，将工具的定义和实现合并。
# FastMCP 会根据函数的签名和文档字符串自动生成工具的 schema。
@mcp.tool()
async def summarize_subtitle_id(
    url: str,
    target_lang: str = "en",
) -> Dict[str, Any]:
    """
    Downloads transcripts from a YouTube URL and returns structured metadata.

    Args:
        url (str): The URL of the YouTube video.
        target_lang (str): The language identifier for the transcript, default is "en".
            This parameter MUST be inferred from the end-user's request language and MUST be one of the codes from the list below.
            For example, If the user's request is English, set it to 'en', If the user's request is in Chinese,  set it to 'zh'.
            DO NOT ask the user for this value.

            Supported language codes:
            - en: English
            - zh: Chinese
            - es: Spanish
            - hi: Hindi
            - ar: Arabic
            - pt: Portuguese
            - ru: Russian
            - ja: Japanese
            - fr: French
            - de: German
            - ko: Korean
            - it: Italian
            - tr: Turkish
            - nl: Dutch
            - pl: Polish
            - vi: Vietnamese
            - th: Thai
            - id: Indonesian
            - ms: Malay
            - fa: Persian
            - ur: Urdu
            - bn: Bengali
            - he: Hebrew
            - fil: Filipino
            - sv: Swedish
            - el: Greek
            - cs: Czech
            - hu: Hungarian
            - da: Danish
            - no: Norwegian
            - fi: Finnish
            - ro: Romanian
            - uk: Ukrainian
            - sr: Serbian

    Returns:
        A dictionary indicating the outcome of the operation.

        On success, the dictionary will contain:
        - status (str): "success"
        - video_id (str): The unique identifier of the YouTube video.
        - title (str): The title of the video.
        - author (str): The channel name of the video's author.
        - description (str): The video's description.
        - length (int): The duration of the video in seconds.
        - available_captions (List[str]): A list of language codes for all available captions.
        - content (str): The text content of the requested transcript.

        On failure, the dictionary will contain:
        - status (str): "failure"
        - reason (str): A message explaining why the operation failed.
    """

    try:
        logging.info(f"正在处理 URL: {url}")
        yt = YouTube(url)
        
        # 调用函数获取元数据和字幕内容
        success, result = dl_caption_byId(yt, target_lang)
        
        if success:
            # 成功时，将状态与元数据合并
            response = {"status": "success"}
            response.update(result)
            return response
        else:
            # 失败时，返回包含原因的字典
            return {"status": "failure", "reason": result}

    except Exception as e:
        # 异常时也返回 None
        error_msg = f"处理 URL {url} 时发生错误: {e}"
        logging.error(error_msg)
        return {"status": "failure", "reason": error_msg}

# 5. 简化服务器启动入口
# FastMCP 极大地简化了服务器的启动过程。
def start_server():
    """服务器启动入口点。"""
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    start_server()
