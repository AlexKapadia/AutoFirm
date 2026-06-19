# =============================================================================
# AutoFirm — single-command test entry point (ADR-001 §3; CLAUDE.md §5.5).
# `make test` runs the gates IN ORDER, FAIL-FAST / FAIL-CLOSED: a red gate (or
# a tool that cannot run) halts forward progress — it is a failed gate, never a
# skipped one (CLAUDE.md §5.6). All invocations use `python -m ...` so the
# toolchain runs identically on the Windows dev box and on Linux CI.
# =============================================================================

PY ?= python

.DEFAULT_GOAL := help
.PHONY: help install test lint types unit coverage mutation sast contract secretscan scripttests clean

# PowerShell host for the ops-script tests (Windows PowerShell 5.1 or pwsh on CI).
PWSH ?= powershell

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

mutation: ## Gate 6: mutation testing — the ACCEPTANCE SIGNAL. FAILS on any survivor.
	# Runs mutmut then grades the cache directly (mutmut's own `results` printer
	# is broken on Python 3.13 + pony-orm) and FAILS CLOSED on any surviving
	# mutant. The full pass over the loop-bearing audit modules is the Linux-CI
	# enforcement plane (see docs/.../E5-tamper-evident-log-results.md); on a
	# native-Windows dev box scope it to the non-loop core, e.g.:
	#   $(PY) scripts/run_mutation_gate.py --paths src/autofirm/audit/rfc6962_hashing.py
	$(PY) scripts/run_mutation_gate.py

sast: ## SAST gate: bandit over runtime code (ADR-001 §4).
	$(PY) -m bandit -q -r src -c pyproject.toml

contract: ## Architecture gate: runtime must not import analysis-only libs (ADR-001 §5).
	$(PY) -m importlinter.cli lint

secretscan: ## Secret-scan gate. Uses gitleaks if present; otherwise a hard fail-closed notice for CI to wire.
	@command -v gitleaks >/dev/null 2>&1 && gitleaks detect --no-banner --redact || \
		echo "WARNING: gitleaks not installed locally — CI MUST run it (fail-closed gate, ADR-001 §4)."

scripttests: ## Ops-script gate: table-driven unit tests for the resume-watchdog decision fn.
	$(PWSH) -NoProfile -ExecutionPolicy Bypass -File tests/test_autofirm_resume_watchdog__decision_table.ps1

# --- The one command (ADR-001 §3): gates run in order, fail-fast. ---
test: lint types unit mutation sast contract secretscan scripttests ## Run the whole gated suite in order.
	@echo "=== make test: all gates complete ==="

clean: ## Remove caches and build artifacts (never touches .autofirm/ or .git/).
	-rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage .coverage.* mutants build *.egg-info
