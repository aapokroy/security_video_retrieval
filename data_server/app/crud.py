"""CRUD operations for the data server."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source, VideoChunk, SourceStatus


async def read_sources(session: AsyncSession) -> list[Source]:
    """Read all sources from the database."""
    result = await session.execute(select(Source))
    return result.scalars().all()


async def read_sources_by_status(session: AsyncSession,
                                 status: SourceStatus) -> list[Source]:
    """Read sources with given status from the database."""
    result = await session.execute(
        select(Source).filter(Source.status_code == status.value)
    )
    return result.scalars().all()


async def read_source(session: AsyncSession, id: int) -> Source:
    """Read source from the database."""
    result = await session.execute(select(Source).filter(Source.id == id))
    return result.scalars().first()


async def create_source(session: AsyncSession,
                        name: str, url: str) -> Source:
    """Create source in the database."""
    source = Source(name=name, url=url, status_code=SourceStatus.PAUSED.value)
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def delete_source(session: AsyncSession, id: int) -> Source:
    """Delete source from the database."""
    source = await read_source(session, id)
    await session.delete(source)
    await session.commit()
    return source


async def update_source_status(session: AsyncSession, id: int,
                               status: SourceStatus, status_msg: str = None
                               ) -> Source:
    """Update source status and status message."""
    source = await read_source(session, id)
    source.status_code = status.value
    source.status_msg = status_msg
    await session.commit()
    return source


async def create_video_chunk(session: AsyncSession, file_path: str,
                             start_time: float, end_time: float,
                             source_id: int) -> VideoChunk:
    """Create video chunk in the database."""
    chunk = VideoChunk(file_path=file_path, start_time=start_time,
                       end_time=end_time, source_id=source_id)
    session.add(chunk)
    await session.commit()
    await session.refresh(chunk)
    return chunk


async def read_video_chunk(session: AsyncSession, id: int) -> VideoChunk:
    """Get video chunk by id."""
    result = await session.execute(
        select(VideoChunk).filter(VideoChunk.id == id)
    )
    return result.scalars().first()


async def read_last_video_chunk(session: AsyncSession, source_id: int
                                ) -> VideoChunk:
    """Get last video chunk of the source."""
    result = await session.execute(
        select(VideoChunk).filter(VideoChunk.source_id == source_id)
        .order_by(VideoChunk.start_time.desc())
    )
    return result.scalars().first()


async def read_video_chunk_by_timestamp(session: AsyncSession,
                                        source_id: int,
                                        timestamp: float) -> VideoChunk:
    """Get video chunk that contains the given timestamp."""
    result = await session.execute(
        select(VideoChunk).filter(VideoChunk.source_id == source_id,
                                  VideoChunk.start_time <= timestamp,
                                  VideoChunk.end_time >= timestamp)
    )
    return result.scalars().first()


async def read_video_chunks_by_interval(session: AsyncSession,
                                        source_id: int,
                                        start_time: float,
                                        end_time: float) -> list[VideoChunk]:
    """Get all video chunks that intersect with the given time interval."""
    result = await session.execute(
        select(VideoChunk).filter(
            VideoChunk.source_id == source_id,
            VideoChunk.end_time >= start_time,
            VideoChunk.start_time <= end_time
        ).order_by(VideoChunk.start_time)
    )
    return result.scalars().all()
