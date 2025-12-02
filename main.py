import os
import tempfile
import logging
from contextlib import asynccontextmanager
from enum import Enum
from typing import AsyncGenerator, Optional, Dict, Any

from fastmcp import FastMCP, Context
from pytubefix import YouTube


from youtube.yt_subtitle_dl import dl_caption_byId
from youtube.yt_audio_dl import dl_audio
from whisper.whisper_deepgram import transcribe_with_deepgram

from utils.constant import MAX_WORKERS_NUMBER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SuccessResponse = Dict[str, Any]
ErrorResponse = Dict[str, str]


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

# 4. 重构工具定义
# 使用 @mcp.tool() 装饰器，将工具的定义和实现合并。
# FastMCP 会根据函数的签名和文档字符串自动生成工具的 schema。
@mcp.tool()
async def download_subtitle_with_id(
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
        - title (str): The title of the video.
        - description (str): The video's description.
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

@mcp.tool
async def audio_transcribe_with_id(url: str) -> Dict[str, Any]:
    """
    Downloads audio from a YouTube URL, transcribes it, and returns the text along with video metadata.

    This tool requires the `PROVIDER` and `API_KEY` environment variables to be set.
    - `PROVIDER`: Specifies the transcription service to use (e.g., "deepgram").
    - `API_KEY`: The API key for the selected provider.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        A dictionary indicating the outcome of the operation.

        On success, the dictionary will contain:
        - status (str): "success"
        - title (str): The title of the video.
        - description (str): The video's description.
        - transcript (str): The full transcribed text of the audio.

        On failure, the dictionary will contain:
        - status (str): "failure" or "error"
        - reason (str): A message explaining why the operation failed (e.g., missing API key, download error, transcription failure).
    """
    provider: str = os.getenv("PROVIDER")
    api_key: str = os.getenv("API_KEY")
    if not provider or not api_key:
        error_response: ErrorResponse = {
            "status": "error",
            "reason": "The process failed because provider and api not be set"
        }
        logging.error("Whisper Provider and API Key must be set")
        return error_response
    original: str = provider

    transcribe_fn = None
    match provider.lower():
        case "deepgram":
            transcribe_fn = transcribe_with_deepgram
        case "cloudflare":
            # Placeholder for future implementation
            pass
        case "groq":
            # Placeholder for future implementation
            pass
        case _:
            logging.error(f"provider {original} must be one of deepgram, cloudflare, groq")
            error_response: ErrorResponse = {
                "status": "error",
                "reason": "The provider must one of deepgram, cloudflare, groq"
            }
            return error_response

    if transcribe_fn is None:
        return {
            "status": "failure",
            "reason": f"Transcription provider '{provider}' is not implemented yet."
        }

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            logging.info(f"Created temporary directory for audio processing: {temp_dir}")
            yt = YouTube(url)
            
            logging.info(f"Downloading audio from {url} to {temp_dir}")
            success, audio_file_path_or_error = dl_audio(yt, temp_dir)

            if not success:
                error_msg = f"Failed to download audio: {audio_file_path_or_error}"
                logging.error(error_msg)
                return {"status": "failure", "reason": error_msg}

            logging.info(f"Starting transcription for {audio_file_path_or_error}")
            transcript = transcribe_fn(
                audio_path=audio_file_path_or_error,
                api_key=api_key,
                temp_dir_path=temp_dir
            )

            if transcript is None:
                return {"status": "failure", "reason": "Transcription process failed."}

            return {
                "status": "success",
                "title": yt.title,
                "description": yt.description,
                "transcript": transcript
            }

        except Exception as e:
            error_msg = f"An error occurred during audio processing for URL {url}: {e}"
            logging.error(error_msg, exc_info=True)
            return {"status": "failure", "reason": error_msg}

def test_deegram_transcribe(filepath: str) -> Dict[str, Any]:
    """
    Transcribes a local audio file using the configured provider (e.g., Deepgram).

    This function mirrors the core logic of `audio_transcribe_with_id` but operates on a local file
    instead of downloading from a URL. It requires the `PROVIDER` and `API_KEY` environment variables.

    Args:
        filepath (str): The path to the local audio file.

    Returns:
        A dictionary with the transcription result or an error.
        - On success: {"status": "success", "transcript": "..."}
        - On failure: {"status": "failure", "reason": "..."}
    """
    api_key: str = os.getenv("API_KEY")


    if not os.path.exists(filepath):
        error_msg = f"File not found: {filepath}"
        logging.error(error_msg)
        return {"status": "failure", "reason": error_msg}


    # Use a temporary directory that the transcription function can use and clean up internally if needed.
    # with tempfile.TemporaryDirectory() as temp_dir:
    temp_dir = tempfile.mkdtemp()
    try:
        logging.info(f"Processing local file: {filepath}")
        logging.info(f"Using temporary directory: {temp_dir}")

        transcript = transcribe_with_deepgram(
            audio_path=filepath,
            api_key=api_key,
            temp_dir_path=temp_dir,
            max_workers=MAX_WORKERS_NUMBER
        )

        if transcript is None:
            return {"status": "failure", "reason": "Transcription process failed."}

        return {
            "status": "success",
            "transcript": transcript
        }

    except Exception as e:
        error_msg = f"An error occurred during local audio processing for {filepath}: {e}"
        logging.error(error_msg, exc_info=True)
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
    # start_server()

    audio_file_path = "/home/jmvoid/Crawler/multi-script-dl/storage/youtube/Scott_Bessent_MAGA_interview.m4a"
    # audio_file_path = "/home/jmvoid/AIProjects/whisper-multiple-api/material/en_xhs_01/temp_0925142138/video_dau_mono.mp3"
    print(f"开始测试文件: {audio_file_path}")
    transcription_result = test_deegram_transcribe(filepath=audio_file_path)
    import json
    print(json.dumps(transcription_result, indent=2, ensure_ascii=False))
