#!/usr/bin/env bash
# Snippet to add to scripts/verify-release.sh.
# Validates every doc-internal link points at a real file.
# Catches DOC-006 (broken docs/README-FULL.pdf) and DOC-S02 (stale CLI screenshot)
# class regressions before push.

set -e

ROOT="$(git rev-parse --show-toplevel)"

echo "[verify-release] Checking internal doc links..."
broken=0
mapfile -t hits < <(grep -rEho '\]\([^)]+\.(md|pdf|html|svg|png|jpg|mmd)\)' \
                       --include="*.md" --include="*.html" \
                       "$ROOT/README.md" "$ROOT/CHANGELOG.md" "$ROOT/CONTRIBUTING.md" "$ROOT/docs/" 2>/dev/null \
                  | sed -E 's|\]\(|:|; s|\)$||')

for line in "${hits[@]}"; do
    file="${line%%:*}"
    target="${line#*:}"
    target="${target%%#*}"
    case "$target" in http*|//*|mailto:*) continue ;; esac
    abs="$(dirname "$file")/$target"
    if [ ! -e "$ROOT/$abs" ] && [ ! -e "$abs" ]; then
        echo "  BROKEN: $file -> $target"
        broken=$((broken + 1))
    fi
done

if [ "$broken" -gt 0 ]; then
    echo "[verify-release] $broken broken doc link(s); release blocked."
    exit 1
fi
echo "[verify-release] Doc-link check passed."
