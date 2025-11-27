import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

from pytubefix import YouTube

def timeout_download(seconds: int = 1):
    """Pauses execution for a specified duration."""
    time.sleep(seconds)


def ffmpeg_split(file_path: str, storage_path: str, time_len: int = 300) -> Tuple[bool, object]:
    """
    使用 ffmpeg 将音频文件分割成多个片段。

    参数:
        file_path (str): 音频文件的路径 (例如 .m4a)。
        storage_path (str): 保存分割后文件的目录。
        time_len (int, optional): 每个片段的时长（秒）。默认为 300。

    返回:
        Tuple[bool, object]: 一个元组，包含：
            -布尔值，表示操作是否成功。
            -如果成功，返回一个包含所有分割文件绝对路径的列表。
            -如果失败，返回一个错误信息字符串。
    """
    # 1. 检查 ffmpeg 是否可用
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg 未安装或未在系统 PATH 中。"

    file_path_obj = Path(file_path)
    storage_path_obj = Path(storage_path)

    # 确保 storage_path 存在
    storage_path_obj.mkdir(parents=True, exist_ok=True)

    # 获取文件名前缀
    file_prefix = file_path_obj.stem

    # 定义输出文件格式
    output_pattern = storage_path_obj / f"{file_prefix}-%03d{file_path_obj.suffix}"

    # 2. 构建并执行 ffmpeg 命令
    command = [
        "ffmpeg",
        "-i", str(file_path_obj),
        "-f", "segment",
        "-segment_time", str(time_len),
        "-ac", "1",
        str(output_pattern)
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
             return False, f"ffmpeg 命令执行失败: {result.stderr}"
    except subprocess.CalledProcessError as e:
        return False, f"ffmpeg 命令执行失败: {e.stderr}"
    except FileNotFoundError:
         return False, "ffmpeg 未安装或未在系统 PATH 中。"

    # 3. 查找已创建的文件并返回其路径
    split_files = sorted(storage_path_obj.glob(f"{file_prefix}-*{file_path_obj.suffix}"))
    split_file_paths = [str(p.resolve()) for p in split_files]

    if not split_file_paths:
        return False, "ffmpeg 命令已执行，但未创建任何文件。请检查 ffmpeg 输出。"

    return True, split_file_paths
