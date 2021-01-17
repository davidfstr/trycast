test:
	python3 -m unittest

testall:
	PYTHONPATH= tox

typecheck:
	mypy

publish:
	poetry build && \
	git tag v$$(cat pyproject.toml | grep version | sed 's/[^0-9.]*//g') && \
	\
	poetry publish && \
	git push origin --tags
