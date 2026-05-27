#!/usr/bin/env bash
set -euo pipefail

# Lightweight script to download and unpack Eclipse JDT LS into a cache
# location. CI should set JDTLS_URL to a specific release tarball/zip to
# ensure reproducibility. The script creates .cache/jdtls/<version>.

CACHE_DIR="${HOME}/.cache/jdtls"
mkdir -p "$CACHE_DIR"

JDTLS_URL=${JDTLS_URL:-}
if [ -z "$JDTLS_URL" ]; then
  echo "Please set JDTLS_URL to a JDT LS distribution URL (CI should pin this)."
  echo "Example: export JDTLS_URL=https://example.org/jdtls.tar.gz"
  exit 1
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading JDT LS from $JDTLS_URL"
curl -sSL "$JDTLS_URL" -o "$TMPDIR/jdtls_dist"

echo "Unpacking to $CACHE_DIR"
if file "$TMPDIR/jdtls_dist" | grep -q "Zip archive"; then
  unzip -q "$TMPDIR/jdtls_dist" -d "$CACHE_DIR"
else
  tar -xzf "$TMPDIR/jdtls_dist" -C "$CACHE_DIR"
fi

echo "JDT LS unpacked into $CACHE_DIR. Configure UML_PLANETATOR_JDTLS to point to launcher jar."
echo "Example: export UML_PLANETATOR_JDTLS=$CACHE_DIR/plugins/org.eclipse.jdt.ls.product/.../launcher.jar"
