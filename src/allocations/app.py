import logging

from fastapi import FastAPI, Request
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


@app.post("/allocate", status_code=201)
async def allocate_endpoint(
    request: Request, allocation: AllocationRequest
) -> dict[str, str]:
    session = get_session()
    batches = repository.SqlAlchemyRepository(session).list()

    line = model.OrderLine(allocation.orderid, allocation.sku, allocation.qty)
    batchref = model.allocate(line, batches)
    return {"batchref": batchref}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello World"}
