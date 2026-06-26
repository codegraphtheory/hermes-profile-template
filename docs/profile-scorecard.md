# Profile quality scorecard

`scripts/profile_scorecard.py` reports whether a Hermes profile distribution is publishable and discovery-ready. It keeps hard validation failures separate from advisory quality warnings.

Run it from a profile repository:

```bash
python3 scripts/profile_scorecard.py .
```

For CI and PR comments:

```bash
python3 scripts/profile_scorecard.py . --json
python3 scripts/profile_scorecard.py . --markdown
make scorecard
```

Exit behavior:

- exits `0` when there are no hard failures, even if advisory warnings are present
- exits `1` when hard failures are present
- exits `2` for command usage problems such as a missing path

Hard failures come from the existing validator and required manifest/env documentation checks. Advisory warnings cover publication and discovery readiness such as README install commands, install smoke instructions, license declaration, GitHub topics, and changelog presence.

## Deterministic JSON contract

`--json` emits a stable object with top-level keys in this order:

```json
{
  "profile": "/absolute/profile/path",
  "summary": {
    "score": 100,
    "total_checks": 8,
    "passed": 8,
    "hard_failures": 0,
    "advisory_warnings": 0
  },
  "checks": []
}
```

Each item in `checks` has this shape:

```json
{
  "id": "readme.install_command",
  "title": "README includes a Hermes install command",
  "severity": "advisory",
  "status": "pass",
  "details": ["README.md contains a hermes profile install command."],
  "remediation": "No action needed."
}
```

Field meanings:

- `severity`: `required` or `advisory`
- `status`: `pass`, `warn`, or `fail`
- `hard_failures`: count of checks with `status: fail`
- `advisory_warnings`: count of checks with `status: warn`
- `score`: `100 - 25 * hard_failures - 5 * advisory_warnings`, clamped at zero

The `checks` array is sorted by check id so repeated runs produce deterministic output.
