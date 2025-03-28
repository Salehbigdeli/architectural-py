from sqlalchemy import text
from sqlalchemy.orm import Session

from allocations.adapters.repository import SqlAlchemyRepository
from allocations.domain import model


def test_repository_can_save_a_batch(session: Session) -> None:
    batch = model.Batch("batch-0", sku="table", qty=10)

    repo = SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = list(
        session.execute(
            text("SELECT reference, sku, _purchased_quantity, eta FROM batches")
        )
    )
    assert rows == [("batch-0", "table", 10, None)]


def insert_order_line(session: Session) -> int:
    session.execute(
        text(
            'INSERT INTO order_lines (orderid, sku, qty) VALUES ("order1", "chair", 12)'
        )
    )
    [[orderline_id]] = session.execute(
        text("SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku"),
        {"orderid": "order1", "sku": "chair"},
    )
    return orderline_id  # type: ignore [no-any-return]


def insert_batch(session: Session, batch_reference: str) -> int:
    session.execute(
        text(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            ' VALUES (:batch_reference, "chair", 100, null)'
        ),
        {"batch_reference": batch_reference},
    )
    [[batch_id]] = session.execute(
        text('SELECT id FROM batches WHERE reference=:batch_reference AND sku="chair"'),
        {"batch_reference": batch_reference},
    )
    return batch_id  # type: ignore [no-any-return]


def insert_allocation(session: Session, orderline_id: int, batch_id: int) -> None:
    session.execute(
        text(
            "INSERT INTO allocations (orderline_id, batch_id)"
            " VALUES (:orderline_id, :batch_id)"
        ),
        {"orderline_id": orderline_id, "batch_id": batch_id},
    )


def test_repository_can_retrieve_a_batch_with_allocations(session: Session) -> None:
    orderline_id = insert_order_line(session=session)
    batch1_id = insert_batch(session=session, batch_reference="batch1")
    insert_batch(session=session, batch_reference="batch2")

    insert_allocation(session=session, orderline_id=orderline_id, batch_id=batch1_id)

    repo = SqlAlchemyRepository(session=session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "chair", 100)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {model.OrderLine("order1", "chair", 12)}


def test_repository_list_returns_all_batches(session: Session) -> None:
    batch1 = model.Batch("batch1", sku="batch_sku", qty=10)
    batch2 = model.Batch("batch2", sku="batch_sku", qty=10)

    repo = SqlAlchemyRepository(session)
    repo.add(batch1)
    repo.add(batch2)

    assert repo.list() == [batch1, batch2]
