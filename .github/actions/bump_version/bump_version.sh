
cd "${PACKAGE}" || exit 1
git config --global user.name 'autobump'

# versioning
OLD_VERSION=$(hatch version)
case "$TYPE" in
  "FIX")
    echo "Bump the version patch"
    hatch version patch
    ;;
  "FEAT")
    echo "Bump the version minor"
    hatch version minor
    ;;
  "RELEASE")
    echo "Bump the version major"
    hatch version major
    ;;
  *)
    echo "Unknown type=$TYPE"
    exit 1
    ;;
esac
NEW_VERSION=$(hatch version)

# git operations
git add "**/__about__.py"
git commit -m "Bump version: $OLD_VERSION → $NEW_VERSION"
git tag "$NEW_VERSION"
git push
git push --tags
