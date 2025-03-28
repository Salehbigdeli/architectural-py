import pytest

from allocations.adapters import repository
from allocations.domain import model
from allocations.service_layer import services


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches: list[model.Batch]):
        self._batches = set(batches)

    def add(self, batch: model.Batch) -> None:
        self._batches.add(batch)

    def get(self, reference: str) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list[model.Batch]:
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self) -> None:
        self.committed = True


def test_returns_allocation() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, eta=None, repo=repo, session=session)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo=repo, session=session)
    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, eta=None, repo=repo, session=session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo=repo, session=session)


def test_commits() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, eta=None, repo=repo, session=session)

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo=repo, session=session)
    assert session.committed is True


def test_add_batch() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, eta=None, repo=repo, session=session)
    assert repo.get("b1") is not None
    assert session.committed is True

