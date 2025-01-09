#!/bin/bash -e
./step1.sh

# read -p build_ready

cd publishme
python3 -m build

# read -p upload_ready
python3 -m twine upload dist/*
cd ..
