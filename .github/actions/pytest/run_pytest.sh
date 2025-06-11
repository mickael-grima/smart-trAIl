#!/usr/bin/env bash

# move to the package
directory="${PARENT}/${NAME}"
cd "$directory" || exit 1

echo "Running test: uv run pytest --cov=\"$SOURCE_CODE\" --cov-config=pyproject.toml -s"
uv run pytest --cov="$SOURCE_CODE" --cov-config=pyproject.toml -s
