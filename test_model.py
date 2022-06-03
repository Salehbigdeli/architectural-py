from datetime import date, timedelta
from typing import Tuple
import pytest

from model import OrderLine, Batch, OrderReference, Quantity, Reference, Sku

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def make_batch_and_line(sku: Sku, batch_qty: Quantity, line_qty: Quantity) -> Tuple[Batch, OrderLine]:
    batch = Batch(Reference('batch-01'), sku, batch_qty)
    line = OrderLine(OrderReference('order-001'), sku, line_qty)
    return batch, line

def test_allocating_to_a_batch_reduces_the_available_quantity():
    b, o = make_batch_and_line('Black-Chair', 20, 2)
    b.allocate(o)
    assert b.available_quantity == 18

def test_can_allocate_if_available_greater_than_required():
    b, o = make_batch_and_line('Black-Chair', 20, 2)
    assert b.can_allocate(o)

def test_cannot_allocate_if_available_smaller_than_required():
    b, o = make_batch_and_line('Black-Chair', 2, 20)
    assert b.can_allocate(o) is False

def test_can_allocate_if_available_equal_to_required():
    b, o = make_batch_and_line('Black-Chair', 2, 2)
    assert b.can_allocate(o)

def test_cannot_allocate_if_sku_mismatch():
    batch = Batch(Reference('batch-01'), Sku('Black-Chair'), 100)
    different_sku_line = OrderLine(OrderReference('order-001'), Sku('Red-Chair'), 2)
    assert batch.can_allocate(different_sku_line) is False

def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line('Black-Chair', 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20

def test_allocation_is_idempotent():
    batch, line = make_batch_and_line('Black-Chair', 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18

# def test_prefers_warehouse_batches_to_shipments():
#     pytest.fail('todo')

# def test_prefers_earlier_batches():
#     pytest.fail('todo')