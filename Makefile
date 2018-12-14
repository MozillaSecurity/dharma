.PHONY: clean clean-test clean-pyc clean-build tag docs lint help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys
for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

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

tag: ## tag version for new release
	VERSION=$$(python3 -c 'import dharma.__version__; print(dharma.__version__)')
	git tag -a v$(VERSION)
	git push origin v$(VERSION)

docs: ## generate Sphinx HTML documentation, including API docs
	sphinx-apidoc -E -f -o docs/source dharma/
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

lint: ## run Pylint
	python3 -m pylint \
		--rcfile=.pylintrc \
		--msg-template='{path}:{line}: [{msg_id}|{obj}] {msg} [pylint: disable={symbol}]' \
		dharma/

servedocs: docs ## watch for changes and compile the docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python3 setup.py install