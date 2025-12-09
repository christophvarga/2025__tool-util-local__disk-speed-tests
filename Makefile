.PHONY: test-report evaluate

test-report:
	@TS=$$(date +%Y%m%d-%H%M); \
	TEST_REPORT_DIR=89_output/test_reports/$$TS; \
	export TEST_REPORT_DIR; \
	mkdir -p "$$TEST_REPORT_DIR"; \
	if [ -f pyproject.toml ] || [ -f requirements.txt ]; then \
		python -m pytest tests --junitxml="$$TEST_REPORT_DIR/junit-py.xml" --cov --cov-report=xml:"$$TEST_REPORT_DIR/coverage-py.xml" || true; \
	fi; \
	if [ -f package.json ]; then \
		npx --yes jest --ci --reporters=default --reporters=jest-junit --outputFile="$$TEST_REPORT_DIR/junit-js.xml" --coverage --coverageDirectory="$$TEST_REPORT_DIR/coverage-js" || true; \
	fi; \
	if [ -f go.mod ]; then \
		go test ./... -coverprofile="$$TEST_REPORT_DIR/coverage-go.out" -json > "$$TEST_REPORT_DIR/go-tests.json" || true; \
	fi; \
	rm -f 89_output/test_reports/latest && ln -s "$$TS" 89_output/test_reports/latest || true; \
	echo "Testartefakte: $$TEST_REPORT_DIR"

# Evaluate results with scripts/evaluate_results.py
# Usage: make evaluate INPUT=/path/to/results.json [TEST_TYPE=...] [OUTPUT=/path/to/report.json]
evaluate:
	@if [ -z "$$INPUT" ]; then \
		echo "Usage: make evaluate INPUT=/path/to/results.json [TEST_TYPE=...] [OUTPUT=/path/to/report.json]"; \
		exit 2; \
	fi; \
	CMD="python scripts/evaluate_results.py --input \"$$INPUT\""; \
	if [ -n "$$TEST_TYPE" ]; then CMD="$$CMD --test-type \"$$TEST_TYPE\""; fi; \
	if [ -n "$$OUTPUT" ]; then CMD="$$CMD --output \"$$OUTPUT\""; fi; \
	echo "$$CMD"; \
	eval $$CMD

