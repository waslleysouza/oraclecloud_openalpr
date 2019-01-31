#!/bin/sh
export PYTHONPATH=modules

pip --no-cache-dir install -r requirements.txt -t ${PYTHONPATH} --upgrade

python app.py