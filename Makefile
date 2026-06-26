.PHONY: deps validate test compile generate-smoke sentence-smoke smoke web-demo release-check scorecard discovery-check demo-smoke clean

PYTHON ?= python3
BASE ?= origin/main
GEN_ROOT ?= /tmp/hermes-profile-template-gen

deps:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate_profile.py .

test:
	$(PYTHON) -m unittest discover -s tests

compile:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m py_compile scripts/*.py

generate-smoke:
	rm -rf $(GEN_ROOT)
	$(PYTHON) scripts/generate_profile.py --params templates/profile.params.yaml --output $(GEN_ROOT)/generated
	$(PYTHON) $(GEN_ROOT)/generated/scripts/validate_profile.py $(GEN_ROOT)/generated

sentence-smoke:
	rm -rf $(GEN_ROOT)
	$(PYTHON) scripts/generate_from_sentence.py --sentence "a database migration reviewer" --output $(GEN_ROOT)/sentence-generated --force
	$(PYTHON) $(GEN_ROOT)/sentence-generated/scripts/validate_profile.py $(GEN_ROOT)/sentence-generated

web-demo:
	$(PYTHON) web-demo/server.py

smoke:
	scripts/smoke_install.sh

release-check:
	$(PYTHON) scripts/release_readiness.py --base $(BASE)

scorecard:
	$(PYTHON) scripts/profile_scorecard.py . --threshold 80

discovery-check:
	$(PYTHON) scripts/discovery_optimizer.py .

demo-smoke:
	$(PYTHON) scripts/demo_fixture.py . --demo generate

clean:
	rm -rf $(GEN_ROOT) .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' \) -delete
