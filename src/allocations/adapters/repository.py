import abc
from typing import Protocol

from sqlalchemy.orm import Session

from allocations.domain import model


class AbstractSession(Protocol):
    def commit(self) -> None:
        raise NotImplementedError  # pragma: no cover


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch) -> None:
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get(self, reference: str) -> model.Batch:
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def list(self) -> list[model.Batch]:
        raise NotImplementedError  # pragma: no cover


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def add(self, batch: model.Batch) -> None:
        self.session.add(batch)

    def get(self, reference: str) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self) -> list[model.Batch]:
        return self.session.query(model.Batch).all()
