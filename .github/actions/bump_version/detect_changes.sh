# Detect whether the version has already changed
# It is important to not update the version for each commit pushed to the PR

# Necessary Environment Variables:
#    - PACKAGE: the path to the package where we want to check the version change
#    - BRANCH_NAME: the branch to which we want to compare main

cd "${PACKAGE}" || exit 1
echo "Comparing branches origin/main against current=${BRANCH_NAME} -- '**/__about__.py'"
changed="$(git diff -z --name-only origin/main..."${BRANCH_NAME}" -- '**/__about__.py')"
if [[ "$changed" ]]
then
  echo "Setting new Github Output: 'version_changed=true'"
  echo "version_changed=true" >> "$GITHUB_OUTPUT"
else
  echo "No changes detected between origin/main and current=${BRANCH_NAME}"
fi
