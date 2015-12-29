all:

.PHONY: install
install:
	pip install -e .

.PHONY: develop
develop: install
	pip install -e ".[test]"

.PHONY: test
test:
	flake8 .
	python -m unittest discover tests/

.PHONY: release
release:
	pip install -e ".[release]"
	fullrelease
