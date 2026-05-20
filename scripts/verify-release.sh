#!/usr/bin/env bash
# Pre-push verification gate. Exits non-zero on any failure.
# Per `feedback_every_project_gets_verification.md`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Auto-activate the project venv if present so ruff/mypy/pytest/build are on PATH
if [ -f ".venv/Scripts/activate" ]; then
  # Windows / Git Bash layout
  # shellcheck disable=SC1091
  source ".venv/Scripts/activate"
elif [ -f ".venv/bin/activate" ]; then
  # POSIX layout
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

step() { printf "\n\033[1;34m==> %s\033[0m\n" "$*"; }
fail() { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*" >&2; exit 1; }
ok()   { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }

step "1. Hard Rule 9 — verify all 6 doc artifacts exist"
for f in README.md CHANGELOG.md CONTRIBUTING.md LICENSE .gitignore docs/index.html; do
  [ -f "$f" ] || fail "missing $f"
done
ok "all 6 doc artifacts present"

step "2. Version sync check"
PYPROJECT_VERSION=$(grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/version = "(.*)"/\1/' | tr -d '\r')
VERSION_PY=$(grep -E '^__version__' agentsuite/__version__.py | sed -E 's/__version__ = "(.*)"/\1/' | tr -d '\r')
[ "$PYPROJECT_VERSION" = "$VERSION_PY" ] || fail "version mismatch: pyproject=$PYPROJECT_VERSION, __version__=$VERSION_PY"
grep -q "$PYPROJECT_VERSION" README.md || fail "README.md does not contain version $PYPROJECT_VERSION"
grep -q "$PYPROJECT_VERSION" USER-MANUAL.md || fail "USER-MANUAL.md does not contain version $PYPROJECT_VERSION"
grep -q "$PYPROJECT_VERSION" docs/index.html || fail "docs/index.html does not contain version $PYPROJECT_VERSION"
grep -q "$PYPROJECT_VERSION" docs/troubleshooting.md || fail "docs/troubleshooting.md does not contain version $PYPROJECT_VERSION"
ok "version aligned across all files: $PYPROJECT_VERSION"

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

step "8.5. Tag-CI gate — confirm test.yml matrix passed on the tag SHA (if tagging a release)"
# This step is the script-gate side of DR-D. It runs only when invoked at
# tag-push time (TAG_SHA in env or detectable via `git describe --exact-match HEAD`).
# When run on a non-tagged HEAD it short-circuits with a notice — the gate
# is forward-looking, fired by the release runbook.
TAG_REF=$(git describe --exact-match HEAD 2>/dev/null || true)
if [ -z "${TAG_SHA:-}" ] && [ -n "$TAG_REF" ]; then
  TAG_SHA=$(git rev-parse "$TAG_REF")
fi

if [ -z "${TAG_SHA:-}" ]; then
  ok "no tag SHA in scope — tag-CI gate deferred (run from a tagged HEAD or set TAG_SHA=<sha>)"
else
  if ! command -v gh >/dev/null 2>&1; then
    fail "tag-CI gate requires the gh CLI; install it before tagging a release"
  fi
  RUNS_JSON=$(gh api "repos/scottconverse/AgentSuite/commits/${TAG_SHA}/check-runs" --paginate)
  # Required job names per DR-D:
  REQUIRED_31X=("unit-integration-golden (3.11)" "unit-integration-golden (3.12)")
  for job in "${REQUIRED_31X[@]}"; do
    CONCLUSION=$(printf '%s' "$RUNS_JSON" | python -c "
import json, sys
data = json.loads(sys.stdin.read())
runs = data.get('check_runs', [])
target = sys.argv[1]
for r in runs:
    if r.get('name') == target:
        print(r.get('conclusion') or 'pending')
        break
else:
    print('missing')
" "$job")
    if [ "$CONCLUSION" != "success" ]; then
      fail "tag-CI gate: job '$job' conclusion='$CONCLUSION' (expected 'success'). Tag SHA ${TAG_SHA}."
    fi
  done
  ok "tag-CI gate: unit-integration-golden (3.11) AND unit-integration-golden (3.12) both SUCCESS at ${TAG_SHA}"
fi

printf "\n\033[1;32mverify-release.sh: ALL CHECKS PASSED — safe to push\033[0m\n"
