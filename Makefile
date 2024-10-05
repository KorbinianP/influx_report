.PHONY: lint
lint:
	pylint $(shell git ls-files '*.py')

.PHONY: test
test:
	@coverage run -m pytest $(shell git ls-files 'test_*.py') && \
	coverage html

.PHONY: sort
sort:
	isort -l 150 $(shell git ls-files 'test_*.py')
	yapf -i $(shell git ls-files 'test_*.py')