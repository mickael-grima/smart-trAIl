#!/usr/bin/env bash

# Given a list of DIRECTORIES, using git, find the ones that have changed files
# return as a python list ([a, b, c]) the directories with changes only

# Necessary Environment Variables:
#    - COMMIT_SHA: the current branch latest commit sha. If empty consider the
#    latest master commit, that will be then compared to the commit before.
#    - DIRECTORIES: the list of directories (space separated) to filter
#    - PARENT_DIRECTORY: the parent directory full path

main_branch='origin/main'

# Get the source commit and the latest master one
source_commit="$COMMIT_SHA"
main_latest_commit=$(git log -n 1 --pretty=format:"%H" "$main_branch")
if [[ ! "$source_commit" ]]
then  # Consider the 2 latest commits in main
  source_commit=$(git log -n 1 --pretty=format:"%H" "$main_branch")
  main_latest_commit=$(git log -n 1 --skip 1 --pretty=format:"%H" "$main_branch")
fi
echo "About to compare $source_commit to $main_latest_commit"


function filter_changed_directories {
  changed_directories="["
  s=""
  for directory in ${DIRECTORIES}; do
    full_directory="$PARENT_DIRECTORY/$directory"
    changed=$(git diff -z --name-only "${main_latest_commit}"..."${source_commit}" -- "$full_directory")
    if [[ $changed ]]
    then
      changed_directories="$changed_directories$s\"$directory\""
      s=", "
    fi
  done
  echo "$changed_directories]"
}

subdirs=$(filter_changed_directories)
echo "changed subdirectories=${subdirs}"
echo "subdirectories=${subdirs}" >> "$GITHUB_OUTPUT"
