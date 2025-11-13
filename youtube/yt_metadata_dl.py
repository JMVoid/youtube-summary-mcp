# import json
# import os
# from pytubefix import YouTube
# from typing import Optional

# def dl_metadata(yt_object: YouTube, store_path: str) -> Optional[str]:
#     """
#     从一个现有的 YouTube 对象中提取元数据并保存为 JSON 文件。
#     """
#     try:
#         caption_codes = [cap.code for cap in yt_object.captions] if yt_object.captions else []
#         metadata_list = list(yt_object.metadata) if yt_object.metadata else []

#         metadata_payload = {
#             "video_id": yt_object.video_id,
#             "title": yt_object.title,
#             "author": yt_object.author,
#             # "publish_date": yt_object.publish_date.isoformat() if yt_object.publish_date else None,
#             "description": yt_object.description,
#             "length": yt_object.length,
#             # "views": yt_object.views,
#             # "rating": yt_object.rating,
#             # "keywords": yt_object.keywords,
#             # "metadata": metadata_list,
#             "available_captions": caption_codes,
#         }

#         file_path = os.path.join(store_path, f"{yt_object.video_id}_metadata.json")
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(metadata_payload, f, ensure_ascii=False, indent=4)
        
#         print(f"元数据已保存: {file_path}")
#         return None

#     except Exception as e:
#         error_msg = f"为视频 ID {yt_object.video_id} 保存元数据时出错: {str(e)}"
#         print(error_msg)
#         return error_msg
