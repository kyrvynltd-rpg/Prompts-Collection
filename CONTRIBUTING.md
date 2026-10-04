# Working on this repo

Private, proprietary project. Branch from `main`, open a pull request, wait for CI (ruff, mypy, tests with 80% coverage floor) before merging. Never commit secrets. Run locally: `pip install -r requirements-dev.txt && ruff check . && mypy && pytest --cov`.
