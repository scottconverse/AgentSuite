#!/usr/bin/env bash
# Regenerate docs/README-FULL.pdf from markdown + Mermaid diagrams.
# Requires: pandoc + mmdc (mermaid-cli) — install hints in CONTRIBUTING.md.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc not found. Install via https://pandoc.org/installing.html"
  exit 1
fi

DIAGRAM_DIR="docs/architecture"
mkdir -p "$DIAGRAM_DIR/rendered"

if command -v mmdc >/dev/null 2>&1; then
  for mmd in "$DIAGRAM_DIR"/*.mmd; do
    [ -e "$mmd" ] || continue
    out="$DIAGRAM_DIR/rendered/$(basename "${mmd%.mmd}").png"
    mmdc -i "$mmd" -o "$out" -b transparent
    echo "rendered $out"
  done
else
  echo "mmdc (mermaid-cli) not found — diagrams will appear as code blocks in PDF"
fi

pandoc \
  README.md docs/USER-MANUAL.md \
  --metadata title="AgentSuite — Full Reference" \
  --metadata author="Scott Converse" \
  --metadata date="$(date +%Y-%m-%d)" \
  --toc --toc-depth=2 \
  --pdf-engine=xelatex \
  -o docs/README-FULL.pdf

echo "wrote docs/README-FULL.pdf"
