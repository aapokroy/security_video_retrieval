"""
Module for capturing frames from source url and writing them into video chunks
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
import time
from datetime import datetime
import urllib.request

import numpy as np
import cv2

from app.config import CHUNKS_DIR, FRAME_SIZE, CHUNK_DURATION, CHUNK_FPS
from app.config import DRAW_TIMESTAMP
from app.database import async_session
from app.models import SourceStatus
from app import models
from app import crud


VIDEO_EXTENSIONS = ['mp4', 'avi']
VIDEO_STREAM_EXTENSIONS = ['mjpg']
IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg']


class SourceCapture(ABC):
    """Abstract context manager for capturing frames from source"""

    def __init__(self, url: str):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def read(self) -> np.ndarray:
        """Read next frame from source"""
        pass


class ImageCapture(SourceCapture):
    """Context manager for capturing frames from image url"""

    def read(self) -> np.ndarray:
        response = urllib.request.urlopen(self.url)
        if self.url.startswith('http') and response.code != 200:
            raise ValueError('Can not read next frame')
        arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        img = cv2.resize(img, FRAME_SIZE)
        return img


class VideoCapture(SourceCapture):
    """
    Context manager for capturing frames from video url.
    Works with video files and video streams.
    Makes sure that video is opened and closed correctly.
    """

    def __init__(self, url: str, is_stream: bool = False):
        super().__init__(url)
        self.frames_total = None
        self.source_fps = None
        self._cap = None
        self._frames_read = 0

    def __enter__(self):
        self._cap = cv2.VideoCapture(self.url)
        if self._cap is None or not self._cap.isOpened():
            raise ValueError('Can not open video capture')
        self.frames_total = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames_total = self.frames_total if self.frames_total > 0 else 0
        self.source_fps = self._cap.get(cv2.CAP_PROP_FPS)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cap.release()

    @property
    def frames_read(self) -> int:
        return self._frames_read

    @frames_read.setter
    def frames_read(self, value: int):
        if self._cap is None:
            raise ValueError('Can be set only in context manager')
        self._frames_read = value
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, value)

    def has_next(self) -> bool:
        """Check if there is next frame"""
        if self._cap is None:
            raise ValueError('Can be checked only in context manager')
        if self.frames_total:
            return self.frames_read < self.frames_total
        else:
            return True

    def skip(self, amount: int):
        """Skip amount of frames"""
        self.frames_read += amount

    def read(self) -> np.ndarray:
        """
        Read next frame from source.
        If source is not stream and there is no next frame, returns None.
        """
        ret, frame = self._cap.read()
        if ret:
            frame = cv2.resize(frame, FRAME_SIZE)
            self.frames_read += 1
            return frame
        else:
            raise ValueError('Can not read next frame')


def open_source(url: str) -> SourceCapture:
    """Get frame capturing context manager for source url"""
    extension = url.lower().split('?')[0].split('.')[-1]
    if extension in VIDEO_STREAM_EXTENSIONS:
        return VideoCapture(url, is_stream=True)
    elif extension in VIDEO_EXTENSIONS:
        return VideoCapture(url)
    elif extension in IMAGE_EXTENSIONS:
        return ImageCapture(url)
    else:
        raise ValueError('Unknown source extension')


class VideoWriter:
    def __init__(self, path: Path):
        self.path = path
        self._is_empty = True

    def __enter__(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._out = cv2.VideoWriter(
            filename=self.path.as_posix(),
            fourcc=fourcc,
            fps=CHUNK_FPS,
            frameSize=FRAME_SIZE
        )
        if self._out is None or not self._out.isOpened():
            raise ValueError('Can not open video writer')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._out.release()
        if self._is_empty:
            self.path.unlink()

    def write(self, frame: np.ndarray):
        """Write frame into video chunk"""
        self._is_empty = False
        self._out.write(frame)


class ChunkWriter(VideoWriter):
    """
    Context manager for writing frames into video chunk.
    Creates video file and database record.
    Makes sure that video file is opened and closed correctly.
    """

    def __init__(self, source_id: int, path: Path):
        super().__init__(path)
        self.source_id = source_id
        self.start_time = None

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError

    async def __aenter__(self):
        super().__enter__()
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        end_time = time.time()
        super().__exit__(exc_type, exc_value, traceback)
        if not self._is_empty:
            async with async_session() as session:
                await crud.create_video_chunk(
                    session=session,
                    file_path=str(self.path),
                    source_id=self.source_id,
                    start_time=self.start_time,
                    end_time=end_time
                )


def add_timestamp(frame: np.ndarray, ts: float) -> np.ndarray:
    """
    Add timestamp to frame.
    Timestamp is a number of seconds since the beginning of the video.
    """

    text = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    color = (255, 255, 255)
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = frame.shape[1] - text_size[0] - 10
    text_y = frame.shape[0] - text_size[1] - 10
    cv2.putText(
        frame,
        text,
        (text_x, text_y),
        font,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA
    )
    return frame


async def process_source(source: models.Source):
    """
    Get frames from source and write them into video chunks.
    Create video files and database records.
    Suppoused to be run as a background task.
    """
    save_dir = CHUNKS_DIR / str(source.id)
    save_dir.mkdir(parents=True, exist_ok=True)
    chunks_count = len(list(save_dir.glob('*.mp4')))
    number_of_frames = int(CHUNK_FPS * CHUNK_DURATION)
    status, status_msg = SourceStatus.FINISHED, None
    try:
        with open_source(source.url) as cap:
            if cap.source_fps and cap.source_fps > CHUNK_FPS:
                skip_frames = int(cap.source_fps / CHUNK_FPS) - 1
            else:
                skip_frames = 0
            while cap.has_next():
                chunk_path = save_dir / f'{chunks_count}.mp4'
                async with ChunkWriter(source.id, chunk_path) as writer:
                    for _ in range(number_of_frames):
                        if not cap.has_next():
                            break
                        read_time = time.time()
                        frame = cap.read()
                        if skip_frames:  # Skip frames to match CHUNK_FPS
                            cap.skip(skip_frames)
                        if DRAW_TIMESTAMP:
                            frame = add_timestamp(frame, read_time)
                        writer.write(frame)
                        delay = 1 / CHUNK_FPS - (time.time() - read_time)
                        if delay > 0:
                            await asyncio.sleep(delay)
                    chunks_count += 1
    except asyncio.CancelledError:
        # Source processing was cancelled by unknown reason,
        # so status should be updated from outside
        return
    except Exception as e:
        status = SourceStatus.ERROR
        status_msg = str(e)
    # Source processing either finished or failed, so status should be updated
    # from inside
    async with async_session() as session:
        await crud.update_source_status(
            session=session,
            id=source.id,
            status=status,
            status_msg=status_msg
        )


class SourceProcessor:
    """Manages background tasks for processing sources."""

    def __init__(self):
        self.tasks = {}

    def add(self, source: models.Source):
        """Start processing source in background task."""
        if source.id in self.tasks:
            raise ValueError('Source is already processing')
        self.tasks[source.id] = asyncio.create_task(
            process_source(source)
        )
        self.tasks[source.id].add_done_callback(
            lambda _: self.tasks.pop(source.id)
        )

    async def remove(self, source_id: int):
        """Stop processing source with given id."""
        if source_id in self.tasks:
            task = self.tasks[source_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def remove_all(self):
        """Stop processing all sources."""
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values())
