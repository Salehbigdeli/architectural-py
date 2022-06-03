from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, String
from sqlalchemy.orm import mapper, relationship

import model


metadata = MetaData()


order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('quantity', Integer, nullable=False),
    Column('order_id', Integer, ForeignKey('orders.id'))
)


def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)