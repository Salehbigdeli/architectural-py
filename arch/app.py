from fastapi import FastAPI
from pydantic import PositiveInt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import model
import orm
import repository


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI(__name__)


@app.post("/allocate", status_code=201)
def allocate_endpoint(orderid: str, sku: str, qty: PositiveInt):
    session = get_session()
    batches = repository.SqlAlchemyRepository(session).list()
    line = model.OrderLine(orderid, sku, qty)

    batchref = model.allocate(line, batches)

    return batchref
