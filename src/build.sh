#!/bin/bash
shiv -e builder.webserver:start -o webserver -E --compile-pyc .
shiv -e builder.worker:start -o worker -E --compile-pyc .
