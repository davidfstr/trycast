path := .

define Comment
	- Run `make help` to see all the available options.
	- Run `make testall` to run all the tests.
	- Run `make lint` to run the linter.
	- Run `make lint-check` to check linter conformity.
	- Run `make publish` to publish to PYPI.
endef


.PHONY: help
help: ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


.PHONY: test
test: ## Run the tests against the current version of Python.
	python3 -m unittest


.PHONY: testall
testall: ## Run the tests against all supported versions of Python.
	PYTHONPATH= tox


.PHONY: publish
publish: ## Publish the package to PYPI.
	poetry build && \
	git tag v$$(cat pyproject.toml | grep version | sed 's/[^0-9.]*//g') && \
	\
	poetry publish && \
	git push origin --tags


.PHONY: lint
lint: black isort flake mypy	## Apply all the linters.


.PHONY: lint-check
lint-check:  ## Check whether the codebase satisfies the linter rules.
	@black --check $(path)
	@isort --check $(path)
	@flake8 $(path)
	@mypy $(path)


.PHONY: black
black: ## Apply black.
	@black --fast $(path)


.PHONY: isort
isort: ## Apply isort.
	@isort $(path)


.PHONY: flake
flake: ## Apply flake8.
	@flake8 $(path)


.PHONY: mypy
mypy: ## Apply mypy.
	@mypy $(path)


.PHONY: coverage
coverage: ## Apply coverage.
	coverage run -m unittest
	coverage html
	open htmlcov/index.html
