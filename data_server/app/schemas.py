"""Pydantic schemas for the data server."""

from pydantic import BaseModel


class VideoChunk(BaseModel):
    id: int
    source_id: int
    file_path: str
    start_time: float
    end_time: float

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "source_id": 1,
                "file_path": "/path/to/chunk.mp4",
                "start_time": 0.0,
                "end_time": 10.0
            }
        }


class Source(BaseModel):
    id: int
    name: str
    url: str
    status_code: int
    status_msg: str | None = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Parking lot",
                "url": "http://example.com/video.mjpg",
                "status_code": 0,
                "status_msg": None
            }
        }
