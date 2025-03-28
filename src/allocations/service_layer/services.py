from datetime import date

from allocations.adapters import repository
from allocations.domain import model


class InvalidSku(Exception):
    pass


def is_valid_sku(sku: str, batches: list[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(
    orderid: str, sku: str, qty: int,
    repo: repository.AbstractRepository,
    session: repository.AbstractSession,
) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batchref = model.allocate(model.OrderLine(orderid, sku, qty), batches)
    session.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: date | None,
    repo: repository.AbstractRepository,
    session: repository.AbstractSession,
) -> None:
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()
