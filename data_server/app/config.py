import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


VIDEOS_DIR = Path(os.getenv('VIDEOS_DIR', './videos')).resolve()
CHUNKS_DIR = VIDEOS_DIR / 'chunks'
SOURCES_DIR = VIDEOS_DIR / 'sources'
TMP_DIR = Path(os.getenv('TMP_DIR', './tmp')).resolve()
FRAME_SIZE = tuple(map(int, os.getenv('FRAME_SIZE', '640x480').split('x')))
CHUNK_DURATION = float(os.getenv('CHUNK_DURATION', 60))
CHUNK_FPS = float(os.getenv('CHUNK_FPS', 1))
DRAW_TIMESTAMP = bool(int(os.getenv('DRAW_TIMESTAMP', 1)))

SOURCES_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
