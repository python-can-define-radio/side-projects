#!/bin/bash -e
echo "Did you bump the version number?"
read -p did_you

git pull
rm -rf publishme
mkdir -p publishme/src
cp -r ../paragradio publishme/src/
cp ../LICENSE publishme/
cp ../README.md publishme/
cp ../pyproject.toml publishme/
