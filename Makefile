test: clean_coverage
	PYTHONPATH=$$PWD HALFORM_CONF_DIR=$$PWD/.config $$PWD/half_orm/packager/test/dummy_test.sh
	PYTHONPATH=$$PWD HALFORM_CONF_DIR=$$PWD/.config pytest --cov-config=.coveragerc --cov=half_orm --cov-report html test

build: clean_build
	python -m build

clean: clean_coverage clean_build

clean_coverage:
	rm -rf htmlcov

clean_build:
	rm -rf dist
