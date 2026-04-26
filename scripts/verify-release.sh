#!/usr/bin/env bash
# Pre-push verification gate. Exits non-zero on any failure.
# Per `feedback_every_project_gets_verification.md`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

step() { printf "\n\033[1;34m==> %s\033[0m\n" "$*"; }
fail() { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*" >&2; exit 1; }
ok()   { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }

step "1. Hard Rule 9 — verify all 6 doc artifacts exist"
for f in README.md CHANGELOG.md CONTRIBUTING.md LICENSE .gitignore docs/index.html; do
  [ -f "$f" ] || fail "missing $f"
done
ok "all 6 doc artifacts present"

step "2. Version sync check"
PYPROJECT_VERSION=$(grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/version = "(.*)"/\1/')
VERSION_PY=$(grep -E '^__version__' agentsuite/__version__.py | sed -E 's/__version__ = "(.*)"/\1/')
[ "$PYPROJECT_VERSION" = "$VERSION_PY" ] || fail "version mismatch: pyproject=$PYPROJECT_VERSION, __version__=$VERSION_PY"
ok "version aligned: $PYPROJECT_VERSION"

step "3. CHANGELOG entry exists for current version"
grep -q "## \[$PYPROJECT_VERSION\]" CHANGELOG.md || fail "CHANGELOG.md missing entry for [$PYPROJECT_VERSION]"
ok "CHANGELOG entry present for $PYPROJECT_VERSION"

step "4. Lint"
ruff check . || fail "ruff check failed"
mypy agentsuite || fail "mypy failed"
ok "lint clean"

step "5. Unit + integration + golden tests"
pytest tests/unit tests/integration tests/golden -v || fail "test suite failed"
ok "tests passing"

step "6. Cleanroom (mocked LLM)"
bash scripts/run-cleanroom.sh || fail "cleanroom failed"
ok "cleanroom passed"

step "7. Build wheel + sdist"
rm -rf dist build *.egg-info
python -m build || fail "build failed"
ls dist/*.whl >/dev/null || fail "wheel not produced"
ls dist/*.tar.gz >/dev/null || fail "sdist not produced"
ok "build artifacts produced"

step "8. Secrets scan (basic)"
if grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build \
     -E 'sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}' . ; then
  fail "potential secret found — review before pushing"
fi
ok "no obvious secrets"

printf "\n\033[1;32mverify-release.sh: ALL CHECKS PASSED — safe to push\033[0m\n"
