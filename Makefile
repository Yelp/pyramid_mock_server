.PHONY: test clean docs

dev:
	tox -e pre-commit install

test:
	tox -e py27,py36

clean:
	find . -type f -iname "*.py[co]" -delete
	find . -name '__pycache__' -delete
	rm -rf *.egg-info/
	rm -rf .tox/
	rm -rf docs/build
	rm .coverage

docs:
	tox -e docs
