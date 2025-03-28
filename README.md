Note: 
1. run `uv pip install -e .`
2. `uv run ruff check --select I --fix .`
3. `uv run ruff format .`
4. `pytest --cov-report term:skip-covered --cov=src tests/`