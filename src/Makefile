.PHONY: all

all:
	. venv/bin/activate && pip install -rrequirements.txt && pip install .
	. venv/bin/activate && pyinstaller -F --hidden-import=flask_api.parsers --hidden-import=flask_api.renderers builder/webserver.py
	. venv/bin/activate && pyinstaller -F builder/worker.py
