from allocations import model, repository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku: str, batches: list[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(
    line: model.OrderLine,
    repo: repository.AbstractRepository,
    session: repository.AbstractSession,
) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref
