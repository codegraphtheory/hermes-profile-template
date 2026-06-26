# Contributor growth backlog

Use this backlog to keep the repository approachable after the first bounty waves. These are unpaid by default unless a maintainer explicitly adds bounty labels and bounty terms to a specific issue.

## Good-first issue ideas

1. Add a README screenshot or linked thumbnail for the X demo video.
   - Labels: `documentation`, `good first issue`, `area:demo`
   - Acceptance: no binary asset unless maintainer approves it, no third-party scripts, demo link remains visible.

2. Add one new generated profile example to `examples/README.md`.
   - Labels: `documentation`, `good first issue`, `area:examples`
   - Acceptance: includes use case, install command with `YOUR_ORG`, keywords, and no real credentials.

3. Add profile prompt examples for one niche workflow.
   - Labels: `documentation`, `good first issue`, `area:discovery`
   - Acceptance: each prompt asks for validation and no real credentials.

4. Improve `docs/launch-kit.md` with one resource-list submission template.
   - Labels: `documentation`, `help wanted`, `area:discovery`
   - Acceptance: target list is relevant and language is not spammy.

5. Add one generated-profile topic bundle to `docs/discovery-metadata.md`.
   - Labels: `documentation`, `good first issue`, `area:discovery`
   - Acceptance: topics are specific, useful, and not keyword-stuffed.

6. Add a `make demo-smoke` transcript to `docs/demos/`.
   - Labels: `documentation`, `help wanted`, `area:demo`
   - Acceptance: transcript uses temporary paths and does not expose local Hermes state.

7. Add a short FAQ answer about why generated profiles need validation.
   - Labels: `documentation`, `good first issue`, `area:quality`
   - Acceptance: answer references `scripts/validate_profile.py` and `hermes profile install`.

8. Add a lightweight release announcement checklist.
   - Labels: `documentation`, `help wanted`, `area:ci`
   - Acceptance: checklist covers validation, CI, changelog, release notes, and fresh install smoke.

## Maintainer rules

- Keep tasks small enough to review quickly.
- Close or retitle issues once the repo changes make them stale.
- Add bounty labels only when the payout amount, wallet requirement, acceptance criteria, and duplicate-PR policy are explicit.
- Preserve first-time contributor credit in commits when work is integrated through a maintainer branch.
