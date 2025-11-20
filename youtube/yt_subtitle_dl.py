
import os
import re
import logging
from pytubefix import YouTube
from typing import Optional, Dict, Any
from collections import defaultdict
from .utils import timeout_download
from constant import TIMEOUT_DOWNLOAD_5

VALID_LANG_CODES  = [
    "en",   # 英语 – 全球通用语，国际交流、科技、互联网主导语言
    "zh",   # 中文 – 母语人数最多，互联网用户庞大，经济影响力强
    "es",   # 西班牙语 – 母语人数第二多，美洲和欧洲广泛使用
    "hi",   # 印地语 – 印度主要语言，母语和使用人口极多（常与英语并用）
    "ar",   # 阿拉伯语 – 覆盖20+国家，宗教、地缘政治重要，但方言差异大
    "pt",   # 葡萄牙语 – 巴西+葡语非洲国家，使用人口超2.5亿
    "ru",   # 俄语 – 东欧、中亚广泛使用，联合国官方语言之一
    "ja",   # 日语 – 日本经济、科技、文化影响力大
    "fr",   # 法语 – 非洲多国官方语言，联合国、外交、国际组织常用语
    "de",   # 德语 – 欧洲最大经济体语言，科技、工程领域重要
    "ko",   # 韩语 – 韩国科技、流行文化（K-pop等）全球影响强
    "it",   # 意大利语 – 欧洲重要语言，文化、艺术、时尚领域影响大
    "tr",   # 土耳其语 – 土耳其及周边，地缘重要，互联网活跃用户多
    "nl",   # 荷兰语 – 荷兰、比利时（弗拉芒）、加勒比地区，国际化程度高
    "pl",   # 波兰语 – 中欧最大语言之一，欧盟重要成员国
    "vi",   # 越南语 – 东南亚人口大国，互联网用户增长迅速
    "th",   # 泰语 – 东南亚重要语言，旅游、区域经济影响
    "id",   # 印尼语 – 东南亚最大国家，人口超2.7亿，国家通用语
    "ms",   # 马来语 – 与印尼语高度互通，马来西亚、新加坡、文莱官方语
    "fa",   # 波斯语（Farsi）– 伊朗、阿富汗（达里语）、塔吉克斯坦，文化悠久
    "ur",   # 乌尔都语 – 巴基斯坦国语，印度大量使用者，与印地语互通度高
    "bn",   # 孟加拉语 – 孟加拉国+印度西孟加拉，母语人数全球第7左右
    "he",   # 希伯来语 – 以色列官方语言，科技创业国家，"iw" 是旧代码
    "fil",  # 菲律宾语（基于他加禄语）– 菲律宾官方语言，英语混合使用广泛
    "sv",   # 瑞典语 – 北欧代表语言，国际化程度高，英语普及率也高
    "el",   # 希腊语 – 欧盟成员国，历史影响深远，区域重要
    "cs",   # 捷克语 – 中欧重要语言，科技、教育水平高
    "hu",   # 匈牙利语 – 欧盟成员国，非印欧语系但科技产业活跃
    "da",   # 丹麦语 – 北欧语言，英语普及率极高，但本身使用范围有限
    "no",   # 挪威语 – 类似丹麦语，北欧语言，高度国际化但本地使用为主
    "fi",   # 芬兰语 – 乌拉尔语系，芬兰官方语言，科技（如诺基亚）有历史影响
    "ro",   # 罗马尼亚语 – 东欧拉丁语族代表，欧盟成员国
    "uk",   # 乌克兰语 – 地缘重要性近年显著提升，使用人口约4000万
    "sr",   # 塞尔维亚语 – 巴尔干地区，与克罗地亚语等互通度高
]


def _srt_content_to_text(srt_content: str) -> str:
    """
    Converts an SRT content string to a plain text string.
    """
    lines = srt_content.strip().split('\n')
    text_lines = []
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')

    for line in lines:
        line = line.strip()
        if not line or line.isdigit() or timestamp_pattern.match(line):
            continue
        text_lines.append(line)
    
    return '\n'.join(text_lines)


def _find_best_caption_for_lang(cap_list: list, lang_code: str) -> Optional[any]:
    """
    根据用户定义的优先级规则从字幕列表中选择最佳字幕。
    优先级:
    1. 通用语言代码 (e.g., 'en')
    2. 特定区域代码 (e.g., 'en-US')
    3. 机器翻译代码 (e.g., 'en.xyz')
    4. 自动语音识别代码 (e.g., 'a.en')
    """
    candidates = {
        'base': None,
        'regional': None,
        'machine': None,
        'auto': None
    }

    for cap in cap_list:
        # 1. 通用语言 (e.g., 'en')
        if cap.code == lang_code:
            if not candidates['base']:
                candidates['base'] = cap
        # 2. 特定区域 (e.g., 'en-US')
        elif '-' in cap.code and '.' not in cap.code:
            if not candidates['regional']:
                candidates['regional'] = cap
        # 3. 机器翻译 (e.g., 'en.*')
        elif '.' in cap.code and not cap.code.startswith('a.'):
            if not candidates['machine']:
                candidates['machine'] = cap
        # 4. 自动语音识别 (e.g., 'a.en')
        elif cap.code.startswith('a.'):
            if not candidates['auto']:
                candidates['auto'] = cap

    # 按优先级返回找到的第一个候选项
    return candidates['base'] or candidates['regional'] or candidates['machine'] or candidates['auto'] or (cap_list[0] if cap_list else None)


def _get_base_lang(caption_code: str) -> Optional[str]:
    """
    从字幕代码中提取基础语言，并使用权威列表进行验证。
    """
    # 1. 优先处理 'a.' 开头的自动生成字幕
    if caption_code.startswith('a.'):
        code_after_a = caption_code[2:]
        if code_after_a in VALID_LANG_CODES:
            return code_after_a
        if code_after_a == 'iw':
            return 'he'
        
    candidate = caption_code.split('-')[0]
    if candidate in VALID_LANG_CODES:
        return candidate
    if candidate == 'iw':
        return 'he'
    candidate = caption_code.split('.')[0]
    if candidate in VALID_LANG_CODES:
        return candidate
    if candidate == 'iw':
        return 'he'
        
    return None

from typing import Optional, Dict, Any, Tuple, Union

def dl_caption_byId(yt_object: YouTube, target_lang: str = "en") -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    获取视频的最佳字幕内容并与元数据合并。
    - 优先获取 target_lang（默认为 "en"）的字幕。
    - 如果指定语言不可用，则按 VALID_LANG_CODES 顺序回退。
    - 如果都不可用，则选择任意一个可用字幕。
    """
    captions = yt_object.captions
    available_codes = [cap.code for cap in captions] if captions else []
    
    if not captions:
        error_msg = f"视频 {yt_object.video_id} 没有可用的字幕"
        logging.error(error_msg)
        return False, error_msg

    logging.info(f"视频 {yt_object.video_id} 的原始可用字幕代码: {available_codes}")

    # 按基础语言对字幕进行分组
    lang_groups = defaultdict(list)
    for cap in captions:
        base_lang = _get_base_lang(cap.code)
        if base_lang:
            lang_groups[base_lang].append(cap)

    # 为每个语言组找到最佳字幕
    best_captions = {}
    for lang, cap_list in lang_groups.items():
        best_cap = _find_best_caption_for_lang(cap_list, lang)
        if best_cap:
            best_captions[lang] = best_cap
    
    logging.info(f"视频 {yt_object.video_id} 的可用字幕语言: {list(best_captions.keys())}")

    lang_to_download = None

    # 1. 尝试获取目标语言
    if target_lang in best_captions:
        lang_to_download = target_lang
    else:
        logging.info(f"未找到指定的语言 '{target_lang}'。将按预设顺序尝试下载。")
        # 2. 按 VALID_LANG_CODES 顺序查找
        for lang_code in VALID_LANG_CODES:
            if lang_code in best_captions:
                lang_to_download = lang_code
                # print(f"找到优先语言 '{lang_code}'。准备下载。")
                break
    
    # 3. 如果还没找到，则随机选一个
    if not lang_to_download and best_captions:
        lang_to_download = list(best_captions.keys())[0]
        logging.info(f"未找到优先语言。随机选择一个可用语言 '{lang_to_download}'。")

    if not lang_to_download:
        error_msg = f"没有找到可供下载的目标语言 (视频ID: {yt_object.video_id})。"
        logging.error(error_msg)
        return False, error_msg

    caption_to_process = best_captions.get(lang_to_download)

    if not caption_to_process:
        error_msg = f"获取字幕 '{lang_to_download}' 失败 (视频ID: {yt_object.video_id})。"
        logging.error(error_msg)
        return False, error_msg

    try:
        # 1. 在内存中获取SRT内容
        timeout_download(TIMEOUT_DOWNLOAD_5)
        srt_content = caption_to_process.generate_srt_captions()
        logging.info(f"成功获取字幕 '{caption_to_process.code}' 的内容 (视频ID: {yt_object.video_id})")

        # 2. 将SRT内容转换为纯文本
        text_content = _srt_content_to_text(srt_content)
        logging.info(f"字幕内容已成功转换为文本。")

        # 3. 构建 metadata_payload
        metadata_payload = {
            "video_id": yt_object.video_id,
            "title": yt_object.title,
            "author": yt_object.author,
            "description": yt_object.description,
            "length": yt_object.length,
            "available_captions": available_codes,
            "content": text_content,
        }
        
        return True, metadata_payload

    except Exception as e:
        error_msg = f"处理字幕 '{caption_to_process.code}' 失败 (视频ID: {yt_object.video_id}): {e}"
        logging.error(error_msg)
        return False, error_msg
