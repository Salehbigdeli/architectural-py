import uuid


def random_sku() -> str:
    return str(uuid.uuid4())


def random_batchref() -> str:
    return str(uuid.uuid4())


def random_orderid() -> str:
    return str(uuid.uuid4())
