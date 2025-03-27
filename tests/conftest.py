import os
import subprocess
import time
from collections.abc import Generator

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

from arch import config
from arch.orm import metadata, start_mappers


@pytest.fixture
def restart_api() -> Generator[None, None, None]:
    """Fixture to start and stop the API server for testing."""
    # Kill any existing uvicorn processes
    subprocess.run(["pkill", "-f", "uvicorn"], check=False)

    # Start the API server
    process = subprocess.Popen(
        ["uvicorn", "arch.app:app", "--host", "localhost", "--port", "5005"],
        preexec_fn=os.setsid,
    )

    # Wait for the server to start
    time.sleep(1)

    # Test if the server is up
    try:
        requests.get(f"{config.get_api_url()}/")
    except requests.ConnectionError as e:
        raise Exception("API server failed to start") from e

    yield

    # Kill the server after the test
    process.kill()
    time.sleep(1)


@pytest.fixture
def in_memory_db() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db: Engine) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()
