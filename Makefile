test:
	python3 -m unittest

typecheck:
	mypy

publish:
	poetry build && poetry publish
	echo "--> Don't forget to create a \"vX.Y.Z\" tag in Git and push it"