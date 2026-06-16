# =============================================================================
# AutoFirm — single-command test entry point (ADR-001 §3; CLAUDE.md §5.5).
# `make test` runs the gates IN ORDER, FAIL-FAST / FAIL-CLOSED: a red gate (or
# a tool that cannot run) halts forward progress — it is a failed gate, never a
# skipped one (CLAUDE.md §5.6). All invocations use `python -m ...` so the
# toolchain runs identically on the Windows dev box and on Linux CI.
# =============================================================================

PY ?= python

.DEFAULT_GOAL := help
.PHONY: help install test lint types unit coverage mutation sast contract secretscan clean

help: ## Show this help.
	@echo "AutoFirm make targets:"
	@echo "  make install   - create .venv and install runtime + dev + test + analysis extras"
	@echo "  make test      - run the full gated pipeline (lint -> types -> tests/cov -> mutation -> sast -> contract -> secrets)"
	@echo "  make mutation  - run mutmut and print the mutation score"

install: ## Create a venv and install all extras (runtime + dev + test + analysis).
	$(PY) -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev,test,analysis]"

# --- Individual gates (ADR-001 §3 order: cheapest + most-likely-to-fail first) ---

lint: ## Gate 1a: ruff lint (self-documenting-name + style gate).
	$(PY) -m ruff check src tests

types: ## Gate 1b: mypy --strict type gate.
	$(PY) -m mypy

unit: ## Gate 3: pytest with branch coverage (unit + property/PBT).
	$(PY) -m pytest

coverage: unit ## Gate 5: coverage gate is enforced by --cov-fail-under in pyproject.

mutation: ## Gate 6: mutation testing — the ACCEPTANCE SIGNAL. Prints the score.
	-$(PY) -m mutmut run
	$(PY) -m mutmut results

sast: ## SAST gate: bandit over runtime code (ADR-001 §4).
	$(PY) -m bandit -q -r src -c pyproject.toml

contract: ## Architecture gate: runtime must not import analysis-only libs (ADR-001 §5).
	$(PY) -m importlinter.cli lint

secretscan: ## Secret-scan gate. Uses gitleaks if present; otherwise a hard fail-closed notice for CI to wire.
	@command -v gitleaks >/dev/null 2>&1 && gitleaks detect --no-banner --redact || \
		echo "WARNING: gitleaks not installed locally — CI MUST run it (fail-closed gate, ADR-001 §4)."

# --- The one command (ADR-001 §3): gates run in order, fail-fast. ---
test: lint types unit mutation sast contract secretscan ## Run the whole gated suite in order.
	@echo "=== make test: all gates complete ==="

clean: ## Remove caches and build artifacts (never touches .autofirm/ or .git/).
	-rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage .coverage.* mutants build *.egg-info
