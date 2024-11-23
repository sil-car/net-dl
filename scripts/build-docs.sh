#!/usr/bin/env bash

scripts_dir="$(dirname "$0")"
repo_dir="$(dirname "$scripts_dir")"
docs_dir="${repo_dir}/sphinx"
cd "$docs_dir" || exit 1
if [[ ! -r ./source/index.rst ]]; then
    echo "PWD=$PWD"
    sphinx-quickstart || exit 1
fi
rm -rf ./build
sphinx-build -b html ./source ./build
