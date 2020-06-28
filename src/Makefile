.PHONY: all

all:
	mkdir -p dist
	venv/bin/pip install -rrequirements.txt && venv/bin/pip install .
	venv/bin/shiv -c webserver -o dist/webserver --site-packages venv/lib/python3.*/site-packages --compile-pyc
	venv/bin/shiv -c worker -o dist/worker --site-packages venv/lib/python3.*/site-packages --compile-pyc
