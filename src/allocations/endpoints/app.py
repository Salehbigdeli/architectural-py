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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()


class AllocationRequest(BaseModel):
    orderid: str
    sku: str
    qty: PositiveInt


def is_valid_sku(sku: str, batches: list[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


@app.post(
    "/allocate", status_code=201, response_model=dict[str, str]
)  # this should not be None
async def allocate_endpoint(
    request: Request, allocation: AllocationRequest
) -> dict[str, str] | JSONResponse:
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    line = model.OrderLine(allocation.orderid, allocation.sku, allocation.qty)
    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return JSONResponse(
            status_code=400,
            content={"message": str(e)},
        )

    return {"batchref": batchref}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello World"}
