py_test:
	export LC_MESSAGES=C PYTHONPATH=$$PWD HALFORM_CONF_DIR=$$PWD/.config && pytest -x -vv --assert=plain --cov-config=.coveragerc --cov=half_orm --cov-report html test

test: clean_coverage py_test

build: clean_build
	python -m build

clean: clean_coverage clean_build

clean_coverage:
	rm -rf htmlcov

clean_build:
	rm -rf dist

publish: build
	twine upload -r half-orm dist/*
