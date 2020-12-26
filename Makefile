.PHONY: clean clean-test clean-pyc clean-build clean_venv docs help venv style lint test test-all coverage show-docs servedocs release dist install check-style check-types show-types
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open(sys.argv[1])
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-venv: ## Removes the venv and artifacts created by make venv (call .venv/)
	rm -rf .venv activate
	find -iname "*.pyc" -delete

clean-docs: ## Removes the sphinx autogenerated documentation
	rm -rf docs/_build docs/modules.rst docs/spotify_playlist_additions.rst

lint: ## check style with flake8
	flake8 --docstring-convention google spotify_playlist_additions tests

test: ## run tests quickly with the default Python
	pytest

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source spotify_playlist_additions -m pytest
	coverage report -m
	coverage html

check-coverage: ## Runs a test to ensure the test % is above 80%
	coverage run --source spotify_playlist_additions -m pytest
	coverage report -m --fail-under=80

show-coverage: coverage ## Shows the coverage report in a browser
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/spotify_playlist_additions.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ spotify_playlist_additions
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

show-docs: docs ## Opens the docs in a browser after creating them
	$(BROWSER) docs/_build/html/index.html

serve-docs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install

venv: .venv/bin/activate ## create a python virtual environment with dependencies and packages installed. Only runs if setup.py or requirements_dex.txt changed

.venv/bin/activate: requirements_dev.txt setup.py requirements.txt
	virtualenv --python=$(shell which python3) .venv
	. .venv/bin/activate; \
	pip install -r requirements_dev.txt; \
	pip install -e .
	# pip install -e . has the same effect as pip instlal -r requirements.txt, except you also get the package here
	ln -sfn .venv/bin/activate activate
	@echo "Use 'source ./activate' to enter virtual environment"

style:  ## styles all code with yapf - google auto styling
	yapf -irp --style pep8 tests spotify_playlist_additions

check-style:  ## Tests that the style is consistent
	yapf -rd --style pep8 tests spotify_playlist_additions

check-types:  ## Does static type checking on the code
	mypy -p spotify_playlist_additions --ignore-missing-imports

show-types: check-types ## Shows the type checking report after running the type checker
	$(BROWSER) .mypyreport/index.html
