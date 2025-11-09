import json
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from pytubefix import YouTube

def timeout_download(seconds: int = 1):
    """Pauses execution for a specified duration."""
    time.sleep(seconds)
