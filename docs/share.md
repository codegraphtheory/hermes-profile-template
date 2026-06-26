# Share hermes-profile-template

Copy-paste snippets for sharing this template. All copy is factual and describes the project as a developer authoring system for Hermes Agent profile distributions.

---

## One-sentence description

> `hermes-profile-template` is a developer authoring system that turns a natural-language prompt into a validated, installable Hermes Agent profile repository.

---

## 280-character post

> Turn a sentence into an installable Hermes Agent profile repo: `hermes-profile-template` generates SOUL.md, config, CI, validation scripts, and docs — then validates the result. github.com/codegraphtheory/hermes-profile-template

---

## Short newsletter blurb

`hermes-profile-template` is an open-source authoring kit for [Hermes Agent](https://github.com/codegraphtheory/hermes) profile distributions. Give it a sentence describing the kind of AI agent you want, and it produces a GitHub-ready repository with identity files, safe configuration, release discipline, and CI validation — ready to install with `hermes profile install`.

The template ships with guided scripts for first-time authors, a quality scorecard, a discovery optimizer, catalog entry generators, and a reusable GitHub Action for generated repos.

Repository: <https://github.com/codegraphtheory/hermes-profile-template>

---

## Maintainer-to-maintainer blurb

If your project needs AI agent profiles, `hermes-profile-template` handles the authoring scaffolding: deterministic generation from a params file or natural-language prompt, profile validation, release guards, and CI. Generated repos include their own `validate_profile.py` and an optional reusable GitHub Actions workflow that calls back to this template. Built for Hermes Agent but the generated file structure is straightforward to adapt.

---

## Example commands

Install and use:

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes

profile-architect chat
```

Validate locally:

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template
python3 -m pip install -r requirements.txt
make validate
```

Generate a profile from the wizard:

```bash
python3 scripts/profile_wizard.py
python3 scripts/generate_profile.py --params profile.params.yaml --output ../my-profile
python3 ../my-profile/scripts/validate_profile.py ../my-profile
```
