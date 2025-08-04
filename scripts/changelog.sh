#!/bin/bash

VERSION=$1
DATE=$(date +%Y-%m-%d)

if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh <version>"
  exit 1
fi

towncrier build --yes --version "$VERSION" --date "$DATE"
