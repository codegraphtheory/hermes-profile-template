.PHONY: deps validate compile generate-smoke action-smoke smoke release-check clean

PYTHON ?= python3
BASE ?= origin/main
GEN_ROOT ?= /tmp/hermes-profile-template-gen

deps:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate_profile.py .

compile:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m py_compile scripts/*.py

generate-smoke:
	rm -rf $(GEN_ROOT)
	$(PYTHON) scripts/generate_profile.py --params templates/profile.params.yaml --output $(GEN_ROOT)/generated
	$(PYTHON) $(GEN_ROOT)/generated/scripts/validate_profile.py $(GEN_ROOT)/generated

action-smoke:
	test -f .github/actions/validate-profile/action.yml
	test -f templates/github-actions/validate-profile.yml
	test -f docs/github-actions-validation.md

smoke:
	scripts/smoke_install.sh

release-check:
	$(PYTHON) scripts/check_release_version.py --base $(BASE)

clean:
	rm -rf $(GEN_ROOT) .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' \) -delete
