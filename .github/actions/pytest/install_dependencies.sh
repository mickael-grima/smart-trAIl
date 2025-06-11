#!/usr/bin/env bash

# install dev dependencies
cd "${DIRECTORY}" || exit 1
uv sync --all-extras --dev
