from sqlalchemy import text
from sqlalchemy.orm import Session

from arch import model


def test_orderline_mapper_can_load_lines(session: Session) -> None:
    session.execute(
        text(
            "INSERT INTO order_lines (orderid, sku, qty) VALUES "
            '("order1", "red-chair", 12),'
            '("order1", "red-table", 1),'
            '("order2", "blue-desk", 1)'
        )
    )
    expected = [
        model.OrderLine("order1", "red-chair", 12),
        model.OrderLine("order1", "red-table", 1),
        model.OrderLine("order2", "blue-desk", 1),
    ]
    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_to_database(session: Session) -> None:
    line = model.OrderLine("order-0", "red-chair", 1)
    session.add(line)
    session.commit()

    rows = list(session.execute(text("SELECT orderid, sku, qty from order_lines")))
    assert rows == [("order-0", "red-chair", 1)]
