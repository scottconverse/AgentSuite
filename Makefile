.PHONY: test test-unit test-integration test-golden test-live cleanroom rerecord-cassettes resnap-golden update-goldens lint

test: test-unit test-integration test-golden

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-golden:
	pytest tests/golden -v

test-live:
	RUN_LIVE_TESTS=1 pytest tests/live -v -m live

cleanroom:
	bash scripts/run-cleanroom.sh

rerecord-cassettes:
	@echo "About to re-record cassettes against real LLM. Press Ctrl+C to abort."
	@sleep 5
	RECORD_CASSETTES=1 pytest tests/integration -v

resnap-golden:
	@echo "About to refresh golden snapshots. Press Ctrl+C to abort."
	@sleep 5
	RESNAP=1 pytest tests/golden -v

# Sprint-plan-named alias for resnap-golden. Same effect: deliberate
# regeneration of committed snapshot fixtures from current mock output.
# Always review the diff before committing the regenerated snapshots.
update-goldens: resnap-golden

lint:
	ruff check .
	mypy agentsuite
