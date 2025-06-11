#!/usr/bin/env bash

pip install 'pre-commit'
cd "$PACKAGE" || exit 1
git ls-files -- "${SOURCE_CODE}" | xargs pre-commit run --color=always --files
