define Comment
	- Run `make help` to see all the available options.
	- Run `make test` to run all tests against the current Python version.
	- Run `make testall` to run all tests against all supported Python versions.
	- Run `make format` to format code.
	- Run `make lint` to check linter conformity.
	- Run `make typecheck` to check typechecker conformity.
	- Run `make publish` to publish to PYPI.
endef


path := .

# ex: "10.14.6" (if on macOS) or "" if not on macOS
macos_version := $(shell which sw_vers > /dev/null 2>&1 && sw_vers -productVersion)

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
publish:  ## Publish the package to PyPI.
	poetry build && \
	poetry publish && \
	\
	git tag v$$(cat pyproject.toml | grep "# publish: version" | sed 's/[^0-9.]*//g') && \
	git push origin --tags


.PHONY: format
format: black isort flake  ## Reformat code.


.PHONY: lint
lint: flake  ## Check whether code satisfies all linter and formatter rules.
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
	mypy --show-error-codes


.PHONY: pyright
pyright:  ## Run pyright typechecker.
	pyright


.PHONY: pyre
# Don't try to run Pyre on macOS 10.14.6 because it doesn't work.
# See: https://github.com/facebook/pyre-check/issues/545
ifneq "$(macos_version)" "10.14.6"
pyre:  ## Run pyre typechecker.
	pyre check
else
pyre:
endif


.PHONY: coverage
coverage:  ## Generate code coverage report.
	coverage run -m unittest
	coverage html
	open htmlcov/index.html
