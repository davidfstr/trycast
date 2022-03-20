define Comment
	- Run `make help` to see all the available options.
	- Run `make testall` to run all the tests.
	- Run `make format` to format code.
	- Run `make lint` to check linter conformity.
	- Run `make publish` to publish to PYPI.
endef


path := .


.PHONY: help
help:  ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


.PHONY: test
test:  ## Run the tests against the current version of Python.
	python3 -m unittest


.PHONY: testall
testall:  ## Run the tests against all supported versions of Python.
	PYTHONPATH= tox


.PHONY: publish
publish: testall  ## Publish the package to PyPI.
	poetry build && \
	git tag v$$(cat pyproject.toml | grep version | sed 's/[^0-9.]*//g') && \
	\
	poetry publish && \
	git push origin --tags


.PHONY: format
format: black isort flake typecheck  ## Reformat code. Run linters.


.PHONY: lint
lint: flake typecheck  ## Check whether code satisfies all linter and formatter rules.
	black --check $(path)
	isort --check $(path)


.PHONY: black
black:  ## Reformat code according to Black style.
	black --fast $(path)


.PHONY: isort
isort:  ## Reformat code such that imports are sorted.
	isort $(path)


.PHONY: flake
flake:  ## Run flake8 linter.
	flake8 $(path)


.PHONY: typecheck
typecheck: mypy pyright pyre  ## Run all typecheckers.


.PHONY: mypy
mypy:  ## Run mypy typechecker.
	mypy


.PHONY: pyright
pyright:  ## Run pyright typechecker.
	pyright


.PHONY: pyre
pyre:  ## Run pyre typechecker.
	pyre check


.PHONY: coverage
coverage:  ## Generate code coverage report.
	coverage run -m unittest
	coverage html
	open htmlcov/index.html
