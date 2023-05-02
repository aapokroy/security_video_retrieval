"""ORM models for the data server."""

from enum import IntEnum

from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class SourceStatus(IntEnum):
    ACTIVE = 0
    PAUSED = 1
    FINISHED = 2
    ERROR = 3


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    status_code = Column(Integer)
    status_msg = Column(String, nullable=True)

    chunks = relationship('VideoChunk', back_populates='source',
                          cascade='all, delete')


class VideoChunk(Base):
    __tablename__ = 'video_chunk'

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True)
    start_time = Column(Float)
    end_time = Column(Float)
    source_id = Column(Integer, ForeignKey('source.id'))

    source = relationship('Source', back_populates='chunks')
