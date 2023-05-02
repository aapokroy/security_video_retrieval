"""Async database configuration and FastAPI dependency"""

import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker


DATABASE_PASSWORD_FILE = os.environ.get('DATABASE_PASSWORD_FILE')
with open(DATABASE_PASSWORD_FILE, 'r') as f:
    DATABASE_PASSWORD = f.read()
DATABASE_URL = 'postgresql+asyncpg://{usr}:{pwd}@db:5432/{db}'.format_map(
    {
        'usr': 'postgres',
        'pwd': DATABASE_PASSWORD,
        'db': 'postgres'
    }
)


engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
