# AdVision AI — one-line entry points.  `make help` lists targets.
PY      ?= .venv/bin/python
PYTHON3 ?= python3.11

.PHONY: help setup test lint verify dataset reports freeze features validate-features analyze dashboard-data dashboard clean

help:            ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-18s %s\n",$$1,$$2}'

setup:           ## create .venv, install deps + Chromium for Playwright
	$(PYTHON3) -m venv .venv && $(PY) -m pip install -U pip && $(PY) -m pip install -r requirements-dev.txt
	$(PY) -m playwright install chromium

test:            ## run the full test suite
	$(PY) -m pytest -q

lint:            ## static checks
	$(PY) -m ruff check src scripts tests config

verify:          ## re-verify every legacy ad ID against its live Ad Library card (polite, 2 workers)
	$(PY) scripts/verify_creatives.py verify --workers 2

dataset:         ## build the validated dataset + evidence reports from live-card evidence
	$(PY) scripts/build_validated_dataset.py && $(PY) scripts/generate_quality_reports.py

freeze:          ## freeze the validated dataset (refuses if any acceptance check fails)
	$(PY) -m src.pipeline.freeze

features:        ## CLIP + OCR + image features for VERIFIED ads
	$(PY) -m src.vision.feature_pipeline --dataset data/processed/validated_dataset.csv --require final_status=VERIFIED

validate-features: ## check feature outputs map 1:1 to the dataset
	$(PY) -m src.vision.feature_pipeline --validate --dataset data/processed/validated_dataset.csv

analyze:         ## features -> clustering -> analytics -> intelligence -> report (needs a frozen dataset)
	$(PY) -m src.pipeline.run --config config/analysis_pipeline.json

dashboard-data:  ## export analysis outputs for the dashboard
	$(PY) -m src.export.dashboard_data

dashboard:       ## run the dashboard locally
	cd dashboard && npm install && npm run dev

clean:           ## remove caches and generated pipeline outputs (keeps all data and evidence)
	find . -path ./.venv -prune -o -name __pycache__ -type d -exec rm -rf {} +
	rm -rf data/outputs
