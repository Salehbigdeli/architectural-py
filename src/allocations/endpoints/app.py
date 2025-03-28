from datetime import date
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, PositiveInt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocations import config
from allocations.adapters import orm, repository
from allocations.domain import model
from allocations.service_layer import services


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()


class AllocationRequest(BaseModel):
    orderid: str
    sku: str
    qty: PositiveInt


class BatchRequest(BaseModel):
    ref: str
    sku: str
    qty: PositiveInt
    eta: date | None


@app.post(
    "/allocate", status_code=201, response_model=dict[str, str]
)
async def allocate_endpoint(
    request: Request, allocation: AllocationRequest
) -> dict[str, str] | JSONResponse:
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    try:
        batchref = services.allocate(
            allocation.orderid, allocation.sku, allocation.qty, repo=repo, session=session
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return JSONResponse(
            status_code=400,
            content={"message": str(e)},
        )

    return {"batchref": batchref}


@app.post("/add_batch", status_code=201)
async def add_batch_endpoint(
    request: Request, batch: BatchRequest
) -> dict[str, str]:
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    services.add_batch(
        batch.ref, batch.sku, batch.qty, batch.eta, repo=repo, session=session
    )
    return {"message": "Ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello World"}
