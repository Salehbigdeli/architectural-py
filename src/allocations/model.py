# from pydantic.dataclasses import dataclass
from dataclasses import dataclass
from datetime import date

from pydantic import PositiveInt


@dataclass(unsafe_hash=True, eq=True)
class OrderLine:  # example of value object
    orderid: str
    sku: str
    qty: PositiveInt


class Batch:  # example of entity object
    def __init__(
        self, ref: str, sku: str, qty: PositiveInt, eta: date | None = None
    ) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: set[OrderLine] = set()

    def allocate(self, line: OrderLine) -> None:
        self._allocations.add(line)

    @property
    def allocated_quantity(self) -> PositiveInt:
        return PositiveInt(sum(line.qty for line in self._allocations))

    @property
    def available_quantity(self) -> PositiveInt:
        return PositiveInt(self._purchased_quantity - self.allocated_quantity)

    def can_allocate(self, line: OrderLine) -> bool:
        if line in self._allocations:
            return True
        return self.sku == line.sku and self.available_quantity >= line.qty

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    def __eq__(
        self, other: object
    ) -> bool:  # this eq and hash are indicators of a entity object
        if not isinstance(other, Batch):
            return False
        return self.reference == other.reference

    def __hash__(self) -> int:
        return hash(self.reference)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            raise ValueError(f"Cannot compare Batch with {type(other)}")
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta


class OutOfStock(Exception):
    pass


def allocate(line: OrderLine, batches: list[Batch]) -> str:  # example of service object
    for batch in sorted(batches):
        if batch.can_allocate(line):
            batch.allocate(line)
            return batch.reference
    raise OutOfStock(f"Out of stock for {line.sku}")
