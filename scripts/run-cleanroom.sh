#!/usr/bin/env bash
# Cleanroom E2E: fresh venv, fresh install, full Founder pipeline against frozen fixture.
# Default: mocked LLM (zero cost). Pass --live for real LLM (gated, capped).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LIVE_MODE=0
if [ "${1:-}" = "--live" ]; then
  LIVE_MODE=1
fi

CLEANROOM_DIR=$(mktemp -d -t agentsuite-cleanroom-XXXXXX)
trap 'rm -rf "$CLEANROOM_DIR"' EXIT

echo "==> cleanroom dir: $CLEANROOM_DIR"

cp -R . "$CLEANROOM_DIR/repo"
cd "$CLEANROOM_DIR/repo"
rm -rf .venv build dist *.egg-info

python -m venv .venv
.venv/Scripts/pip install -e .[dev] >/dev/null

OUTPUT_DIR="$CLEANROOM_DIR/output"
mkdir -p "$OUTPUT_DIR"
export AGENTSUITE_OUTPUT_DIR="$OUTPUT_DIR"

if [ "$LIVE_MODE" -eq 1 ]; then
  echo "==> live mode: will use resolve_provider() — costs money"
  export AGENTSUITE_COST_CAP_USD=5.0
  unset AGENTSUITE_LLM_PROVIDER_FACTORY
else
  echo "==> mocked mode: AGENTSUITE_LLM_PROVIDER_FACTORY=agentsuite.llm.mock:_default_mock_for_cli"
  export AGENTSUITE_LLM_PROVIDER_FACTORY="agentsuite.llm.mock:_default_mock_for_cli"
fi

.venv/Scripts/agentsuite founder run \
  --business-goal "Launch PatentForgeLocal v1" \
  --project-slug "pfl-cleanroom" \
  --inputs-dir "$REPO_ROOT/examples/patentforgelocal" \
  --run-id "cleanroom-r1"

# Assert 26 artifacts present
RUN_DIR="$OUTPUT_DIR/runs/cleanroom-r1"
EXPECTED=(
  "_state.json"
  "inputs_manifest.json"
  "extracted_context.json"
  "consistency_report.json"
  "export-manifest-template.json"
  "qa_report.md"
  "qa_scores.json"
  "brand-system.md"
  "founder-voice-guide.md"
  "product-positioning.md"
  "audience-map.md"
  "claims-and-proof-library.md"
  "visual-style-guide.md"
  "campaign-production-workflow.md"
  "asset-qa-checklist.md"
  "reusable-prompt-library.md"
)
TEMPLATES=(
  "landing-hero.md"
  "readme-graphic.md"
  "launch-announce.md"
  "investor-one-pager.md"
  "municipal-buyer-email.md"
  "product-explainer.md"
  "social-graphic.md"
  "conference-slide.md"
  "press-pitch.md"
  "demo-script.md"
  "comparison-page.md"
)
MISSING=0
for f in "${EXPECTED[@]}"; do
  [ -f "$RUN_DIR/$f" ] || { echo "[MISS] $f"; MISSING=$((MISSING+1)); }
done
for t in "${TEMPLATES[@]}"; do
  [ -f "$RUN_DIR/brief-template-library/$t" ] || { echo "[MISS] brief-template-library/$t"; MISSING=$((MISSING+1)); }
done
[ "$MISSING" -eq 0 ] || { echo "==> CLEANROOM FAIL: $MISSING artifact(s) missing"; exit 1; }

# MCP smoke
.venv/Scripts/python -c "from agentsuite.mcp_server import build_server; s = build_server(); assert 'founder_run' in s.tool_names()"

# Approve to test promotion
.venv/Scripts/agentsuite founder approve --run-id cleanroom-r1 --approver cleanroom --project-slug pfl-cleanroom
[ -f "$OUTPUT_DIR/_kernel/pfl-cleanroom/brand-system.md" ] || { echo "[MISS] _kernel promotion"; exit 1; }

echo "==> CLEANROOM PASS — 26 artifacts + MCP smoke + approval promotion all OK"
