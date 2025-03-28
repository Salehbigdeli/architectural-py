from datetime import date, timedelta

import pytest
from pydantic import PositiveInt

from allocations.domain.model import Batch, OrderLine, OutOfStock, allocate

today = date.today()
tommorow = today + timedelta(days=1)
later = today + timedelta(days=100)


def test_allocating_to_a_batch_reduces_the_available_quantity() -> None:
    batch = Batch("batch-001", "Small-table", qty=PositiveInt(20), eta=today)
    line = OrderLine(orderid="order-ref", sku="Small-table", qty=PositiveInt(2))

    batch.allocate(line)

    assert batch.available_quantity == 18


def make_batch_and_line(
    sku: str, batch_qty: PositiveInt, line_qty: PositiveInt
) -> tuple[Batch, OrderLine]:
    return (
        Batch("batch-01", sku=sku, qty=batch_qty, eta=today),
        OrderLine(orderid="order-001", sku=sku, qty=line_qty),
    )


def test_can_allocate_if_available_greater_than_required() -> None:
    large_batch, small_line = make_batch_and_line(
        "elegant-lamp", PositiveInt(100), PositiveInt(10)
    )
    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_smaller_than_required() -> None:
    small_batch, large_line = make_batch_and_line(
        "table", PositiveInt(10), PositiveInt(100)
    )
    assert small_batch.can_allocate(large_line) is False


def test_can_allocate_if_available_equal_to_required() -> None:
    batch, line = make_batch_and_line("chair", PositiveInt(10), PositiveInt(10))
    assert batch.can_allocate(line)


def test_cannot_allocate_if_sku_dont_match() -> None:
    batch = Batch("Batch-002", sku="table", qty=PositiveInt(100), eta=today)
    line = OrderLine(orderid="order-id", sku="chair", qty=PositiveInt(10))
    assert batch.can_allocate(line) is False


def test_can_only_deallocate_allocated_lines() -> None:
    batch, unallocated_line = make_batch_and_line(
        "Not-allocated-yet", PositiveInt(20), PositiveInt(2)
    )
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20


def test_deallocating_allocated_line() -> None:
    batch, line = make_batch_and_line("chair", PositiveInt(20), PositiveInt(2))
    batch.allocate(line)
    batch.deallocate(line)

    assert batch.available_quantity == 20


def test_allocation_is_idempotent() -> None:
    batch, line = make_batch_and_line("table", PositiveInt(20), PositiveInt(2))
    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18


def test_prefers_current_stock_batches_to_shipments() -> None:
    in_stock_batch = Batch("in-stock-batch", sku="chair", qty=20)
    shipment_batch = Batch("shipment-batch", sku="chair", qty=20, eta=tommorow)
    line = OrderLine("orderid", sku="chair", qty=2)

    allocate(line, [shipment_batch, in_stock_batch])

    assert in_stock_batch.available_quantity == 18
    assert shipment_batch.available_quantity == 20


def test_prefer_earlier_batch() -> None:
    earliest_batch = Batch("shipment-batch", sku="chair", qty=20, eta=today)
    medium_eta_batch = Batch("medium-eta-batch", sku="chair", qty=20, eta=tommorow)
    latest_batch = Batch("latest-batch", sku="chair", qty=20, eta=later)

    line = OrderLine("order-id", "chair", 2)
    allocate(line, [medium_eta_batch, earliest_batch, latest_batch])

    assert earliest_batch.available_quantity == 18
    assert medium_eta_batch.available_quantity == 20
    assert latest_batch.available_quantity == 20


def test_allocate_returns_allocated_batch_ref() -> None:
    in_stock_batch = Batch("shipment-batch", sku="chair", qty=20)
    later_batch = Batch("late-batch", sku="chair", qty=20, eta=later)

    line = OrderLine("order-id", "chair", 2)
    allocation_ref = allocate(line, [in_stock_batch, later_batch])
    assert allocation_ref == in_stock_batch.reference


def test_can_allocate_already_allocated_order() -> None:
    in_stock_batch = Batch("shipment-batch", sku="chair", qty=20)
    line = OrderLine("order-id", "chair", 20)

    allocate(line, [in_stock_batch])
    allocate(line, [in_stock_batch])


def test_raises_out_of_stock_if_cannot_allocate() -> None:
    in_stock_batch = Batch("shipment-batch", sku="chair", qty=20)
    line = OrderLine("order-id", "chair", 20)

    allocate(line, [in_stock_batch])

    with pytest.raises(OutOfStock, match="chair"):
        allocate(OrderLine("order-id-2", "chair", 20), [in_stock_batch])
