import os
from pathlib import Path
import re
import shutil
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, Depends
from fastapi.responses import Response, FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import cv2

from app import crud, schemas
from app.models import SourceStatus
from app.video_processing import SourceProcessor, VideoCapture, VideoWriter
from app.database import async_session
from app.config import TMP_DIR, SOURCES_DIR, CHUNKS_DIR, CHUNK_FPS


# FastAPI Dependencies
class TmpFilePath:
    """FastAPI dependency for getting temporary file path"""

    def __init__(self, extension: str) -> Path:
        self.extension = extension

    def __call__(self) -> Path:
        path = TMP_DIR / f'{uuid.uuid4()}{self.extension}'
        try:
            yield path
        finally:
            if path.exists():
                path.unlink()


async def get_session() -> AsyncSession:
    """FastAPI dependency to get a database session"""
    async with async_session() as session:
        yield session


# Server lifecycle management
source_processor = SourceProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI app lifespan context manager"""
    async with async_session() as session:
        active_sources = await crud.read_sources_by_status(
            session, SourceStatus.ACTIVE
        )
        for source in active_sources:
            source_processor.add(source)
    yield
    await source_processor.remove_all()


# FastAPI app configuration
tags_metadata = [
    {
        "name": "Source management",
        "description": "Manage video sources."
    },
    {
        "name": "Retrieve video data",
        "description": "Retrieve video segments and frames."
    }
]


description = """
Example of a CCTV data server for **Video Retrieval System**.

You can process videos (Streams, Videos, Images) into smaller chunks
and send them to the RabbitMQ queue.
"""


app = FastAPI(
    title="CCTV Data Server",
    description=description,
    version="0.1.0",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/mit-license.php"
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url="/docs")


# Source management
@app.get(
    "/sources/list",
    response_model=list[schemas.Source],
    tags=["Source management"],
    summary="Get list of all sources",
    response_description="List of all sources"
)
async def get_sources(session: AsyncSession = Depends(get_session)):
    """
    Get list of all sources.
    """
    sources = await crud.read_sources(session)
    return sources


@app.post(
    "/sources/add/url",
    response_model=schemas.Source,
    tags=["Source management"],
    summary="Create source from url",
    response_description="Source created"
)
async def create_source_from_url(name: str, url: str,
                                 session: AsyncSession = Depends(get_session)):
    """
    Create source from url.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **url**: url of the source, must be accessible. Supported extensions:
        - video: mp4, avi
        - video stream: mjpg
        - image: png, jpg, jpeg
    """
    source = await crud.create_source(session, name, url)
    return source


@app.post(
    "/sources/add/file",
    response_model=schemas.Source,
    tags=["Source management"],
    summary="Create source from file",
    response_description="Source created"
)
async def create_source_from_file(name: str,
                                  file: UploadFile,
                                  session: AsyncSession = Depends(get_session)
                                  ):
    """
    Create source from file.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **file**: video file. Supported extensions: mp4, avi
    """
    file_name = file.filename.replace(' ', '_')
    file_name = re.sub(r'[^a-zA-Z0-9_.-]', '', file_name)
    path = SOURCES_DIR / file_name
    count = 1
    while path.is_file():
        name, ext = os.path.splitext(file_name)
        path = SOURCES_DIR / f'{name}_{count}{ext}'
        count += 1
    with open(path, 'wb') as out_file:
        while content := file.file.read(1024):
            out_file.write(content)
    source = await crud.create_source(session, name, path.as_uri())
    return source


@app.put(
    "/sources/start",
    tags=["Source management"],
    summary="Start source"
)
async def start_source(id: int, session: AsyncSession = Depends(get_session)):
    """
    Start source processing in background:
    - Get frames from source url
    - Save frames to disk as video chunks
    - Create database records for video chunks
    - Send video chunks to RabbitMQ queue

    Parameters:
    - **id**: source id
    """
    source = await crud.read_source(session, id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source already active")
    await crud.update_source_status(session, id, SourceStatus.ACTIVE)
    source_processor.add(source)


@app.put(
    "/sources/pause",
    tags=["Source management"],
    summary="Pause source"
)
async def pause_source(id: int, session: AsyncSession = Depends(get_session)):
    """
    Pause source processing.

    Parameters:
    - **id**: source id
    """
    source = await crud.read_source(session, id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code != SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source not active")
    if source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    await source_processor.remove(id)
    await crud.update_source_status(session, id, SourceStatus.PAUSED)


@app.put(
    "/sources/finish",
    tags=["Source management"],
    summary="Finish source"
)
async def finish_source(id: int, session: AsyncSession = Depends(get_session)):
    """
    Finish source processing. Finished source can't be started again.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Parameters:
    - **id**: source id
    """
    source = await crud.read_source(session, id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    if source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.update_source_status(session, id, SourceStatus.FINISHED)


@app.delete(
    "/sources/remove",
    tags=["Source management"],
    summary="Remove source"
)
async def remove_source(id: int, session: AsyncSession = Depends(get_session)):
    """
    Remove source.
    Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.
    """
    source = await crud.read_source(session, id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.delete_source(session, id)  # Chunks are deleted by cascade
    if source.url.startswith('file://'):  # Delete source file if local
        path = Path(source.url[7:])
        path.unlink()
    shutil.rmtree(CHUNKS_DIR / str(id))  # Delete video chunks


# Video management
@app.get(
    "/videos/get/chunk",
    tags=["Retrieve video data"],
    summary="Get video chunk",
    response_description="Video chunk",
    response_class=FileResponse
)
async def get_video_chunk(chunk_id: int,
                          session: AsyncSession = Depends(get_session)):
    """
    Get video chunk from disk.

    Parameters:
    - **chunk_id**: video chunk id
    """
    chunk = await crud.read_video_chunk(session, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Video chunk not found")
    return FileResponse(path=chunk.file_path,
                        filename=f'{chunk.source_id}_{chunk_id}.mp4',
                        media_type="video/mp4")


@app.get(
    "/videos/get/frame",
    tags=["Retrieve video data"],
    summary="Get frame by timestamp",
    response_description="Frame",
    response_class=Response
)
async def get_frame(source_id: int, timestamp: float,
                    session: AsyncSession = Depends(get_session)):
    """
    Get frame from source by timestamp.

    Parameters:
    - **source_id**: source id
    - **timestamp**: timestamp in seconds
    """
    chunk = await crud.read_video_chunk_by_timestamp(session, source_id,
                                                     timestamp)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    with VideoCapture(chunk.file_path) as cap:
        frame_number = int((timestamp - chunk.start_time) * CHUNK_FPS)
        cap.skip(frame_number)
        frame = cap.read()
        _, buffer = cv2.imencode('.jpg', frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")


@app.get(
    "/videos/get/segment",
    tags=["Retrieve video data"],
    summary="Get video segment by time interval",
    response_description="Video segment",
    response_class=FileResponse
)
async def get_video_segment(source_id: int, start_time: float, end_time: float,
                            tmp_path: Path = Depends(TmpFilePath('.mp4')),
                            session: AsyncSession = Depends(get_session)):
    """
    Get video segment from source by time interval.
    Resulting video may contain gaps, if source was paused during processing.

    Parameters:
    - **source_id**: source id
    - **start_time**: start timestamp in seconds
    - **end_time**: end timestamp in seconds
    """
    chunks = await crud.read_video_chunks_by_interval(
        session, source_id, start_time, end_time
    )
    if not chunks:
        raise HTTPException(status_code=404, detail="Video segment not found")
    with VideoWriter(tmp_path) as out:
        for i, chunk in enumerate(chunks):
            uri = Path(chunk.file_path).as_uri()
            with VideoCapture(uri) as cap:
                if i == 0 and start_time > chunk.start_time:
                    # Skip frames before start_time
                    cap.skip(int((start_time - chunk.start_time) * CHUNK_FPS))
                if i == len(chunks) - 1 and end_time < chunk.end_time:
                    # Skip frames after end_time
                    cap.frames_total = \
                        int((end_time - chunk.start_time) * CHUNK_FPS)
                while cap.has_next():
                    frame = cap.read()
                    out.write(frame)
    return FileResponse(path=tmp_path,
                        filename='{}_{}_{}.mp4'.format(
                            source_id, int(start_time), int(end_time)
                        ),
                        media_type="video/mp4")
