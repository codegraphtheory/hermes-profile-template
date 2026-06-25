.PHONY: deps validate compile generate-smoke smoke test smoke-wizard release-check clean

PYTHON ?= python3
BASE ?= origin/main
GEN_ROOT ?= /tmp/hermes-profile-template-gen

deps:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate_profile.py .
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

compile:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m py_compile scripts/*.py

generate-smoke:
	rm -rf $(GEN_ROOT)
	$(PYTHON) scripts/generate_profile.py --params templates/profile.params.yaml --output $(GEN_ROOT)/generated
	$(PYTHON) $(GEN_ROOT)/generated/scripts/validate_profile.py $(GEN_ROOT)/generated

smoke:
	scripts/smoke_install.sh
	$(MAKE) smoke-wizard

smoke-wizard:
	$(PYTHON) scripts/profile_wizard.py --non-interactive --name smoke-wizard-profile --description "Testing wizard smoke." --output /tmp/smoke-wizard-out
	$(PYTHON) scripts/validate_profile.py /tmp/smoke-wizard-out
	rm -rf /tmp/smoke-wizard-out

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

release-check:
	$(PYTHON) scripts/release_readiness.py --base $(BASE)

clean:
	rm -rf $(GEN_ROOT) .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' \) -delete
