from dataclasses import dataclass
from datetime import date
from typing import List, NewType, Optional, Set


class Quantity(int):
    pass


class Sku(str):
    pass


class Reference(str):
    pass

class OrderReference(str):
    pass


@dataclass(frozen=True)
class OrderLine:
    orderid: OrderReference
    sku: Sku
    quantity: Quantity


class Batch:
    def __init__(self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]=None):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: Set[OrderLine] = set()

    def allocate(self, orderline: OrderLine):
        if self.can_allocate(orderline):
            self._allocations.add(orderline)
    

    def deallocate(self, orderline: OrderLine):
        if orderline in self._allocations:
            self._allocations.remove(orderline)

    @property
    def allocated_quantity(self):
        return sum(orderline.quantity for orderline in self._allocations)

    @property
    def available_quantity(self) -> Quantity:
        return self._purchased_quantity - self.allocated_quantity
    

    def can_allocate(self, orderline: OrderLine):
        if orderline.sku != self.sku:
            return False
        return self.available_quantity >= orderline.quantity

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Batch):
            return False
        return self.reference == o.reference

    def __hash__(self) -> int:
        return hash(self.reference)


def allocate(orderline: OrderLine, batches: List[Batch]):
    batch = next(
        b for b in sorted(batches) if b.can_allocate(orderline)
    )
    batch.allocate(orderline)
    return batch.reference
