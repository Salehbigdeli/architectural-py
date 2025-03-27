FROM python:3.12-alpine

# RUN apt install gcc libpq (no longer needed bc we use psycopg2-binary)

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /code
COPY src /code
WORKDIR /code
CMD ["uvicorn", "allocations.app:app", "--reload", "--host", "0.0.0.0", "--port", "5002"]