#!/bin/sh

PYTHONPATH=$PYTHONPATH:./lib/pymaker:./lib/pyexchange py.test --cov=keeper --cov=inventory_keeper --cov-report=term --cov-append tests/
