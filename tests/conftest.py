import time
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
import requests
from requests.exceptions import ConnectionError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

from allocations import config
from allocations.adapters.orm import metadata, start_mappers


@pytest.fixture
def restart_api() -> None:
    Path(__file__).parent.parent.joinpath(
        "src", "allocations", "endpoints", "api.py"
    ).touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


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


def wait_for_postgres_to_come_up(engine: Engine) -> Connection | None:
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


def wait_for_webapp_to_come_up() -> requests.Response | None:
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")


@pytest.fixture(scope="session")
def postgres_db() -> Engine:
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session(postgres_db: Engine) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


@pytest.fixture
def add_stock(
    postgres_session: Session,
) -> Generator[Callable[[list[tuple[str, str, int, str | None]]], None], None, None]:
    batches_added = set()
    skus_added = set()

    def _add_stock(lines: list[tuple[str, str, int, str | None]]) -> None:
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                text(
                    "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                    " VALUES (:ref, :sku, :qty, :eta)"
                ),
                {"ref": ref, "sku": sku, "qty": qty, "eta": eta},
            )

            [[batch_id]] = postgres_session.execute(
                text("SELECT id FROM batches WHERE reference=:ref AND sku=:sku"),
                {"ref": ref, "sku": sku},
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        postgres_session.execute(
            text("DELETE FROM allocations WHERE batch_id=:batch_id"),
            {"batch_id": batch_id},
        )
        postgres_session.execute(
            text("DELETE FROM batches WHERE id=:batch_id"),
            {"batch_id": batch_id},
        )
    for sku in skus_added:
        postgres_session.execute(
            text("DELETE FROM order_lines WHERE sku=:sku"),
            {"sku": sku},
        )
        postgres_session.commit()
