.PHONY: lint
lint:
	ruff check .

.PHONY: format
format:
	ruff format .

.PHONY: test
test:
	@coverage run -m pytest && coverage html

.PHONY: check
check: lint test