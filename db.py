"""Database connection."""

import os
from urllib.parse import urlparse

import asyncpg

# Set by connect() when the server starts.
pool: asyncpg.Pool


async def connect() -> None:
    global pool
    url = os.environ["DEMO_DATABASE_URL"]
    if urlparse(url).path not in ("/vent_demo", "/vent_demo_big"):
        raise RuntimeError("DEMO_DATABASE_URL must name an isolated demo database")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
