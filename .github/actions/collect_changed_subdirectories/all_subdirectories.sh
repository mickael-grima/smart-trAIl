#!/usr/bin/env bash

# List everything under DIRECTORY & keep the dir ones only

# Necessary Environment Variables:
#    - DIRECTORY: the list of directories (space separated) to filter

subdirs=$(find "${DIRECTORY}" -maxdepth 1  -mindepth 1 -type d | sed 's:.*/::')

# format
res="["
s=""
for subdir in ${subdirs}
do
  echo "Subdirectory=${subdir}; PARENT=${DIRECTORY}"
  res="$res$s\"$subdir\""
  s=", "
done
res="$res]"

echo "subdirectories=$res"
echo "subdirectories=$res" >> "$GITHUB_OUTPUT"
