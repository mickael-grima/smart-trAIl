#!/usr/bin/env bash

# Chek whether the .pre-commit-config.yaml config file exists

# Environment to provide:
#   PACKAGE: the full path (from git root) to the package/service

cd "${PACKAGE}" || exit 1
if ls -a | grep '.pre-commit-config.yaml'
then
  echo "Set Output: has_config=true"
  echo "has_config=true" >> "$GITHUB_OUTPUT"
else
  echo "Set Output: has_config=false"
  echo "has_config=false" >> "$GITHUB_OUTPUT"
fi
