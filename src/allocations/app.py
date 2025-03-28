import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, PositiveInt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocations import config, model, orm, repository

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


@app.post("/allocate", status_code=201)
async def allocate_endpoint(
    request: Request, allocation: AllocationRequest
) -> dict[str, str] | JSONResponse:
    session = get_session()
    batches = repository.SqlAlchemyRepository(
        session
    ).list()  # the name is not good here, it's not visible that it's a list of batches!

    if not is_valid_sku(allocation.sku, batches):
        return JSONResponse(
            status_code=400, content={"message": f"Invalid sku {allocation.sku}"}
        )

    line = model.OrderLine(allocation.orderid, allocation.sku, allocation.qty)
    try:
        batchref = model.allocate(line, batches)
    except model.OutOfStock:
        return JSONResponse(
            status_code=400,
            content={"message": f"Out of stock for sku {allocation.sku}"},
        )

    session.commit()
    return {"batchref": batchref}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello World"}
