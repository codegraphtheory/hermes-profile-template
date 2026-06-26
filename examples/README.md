# Hermes profile examples

These lightweight examples show publishable profile shapes without including real credentials or runtime state.

| Example | Use case | Install command | Keywords |
| --- | --- | --- | --- |
| `security-reviewer` | Reviews code and architecture for application security risk. | `hermes profile install github.com/YOUR_ORG/security-reviewer --alias` | security, code review |
| `database-migration-reviewer` | Reviews SQL migrations for rollout and rollback risk. | `hermes profile install github.com/YOUR_ORG/database-migration-reviewer --alias` | database, migrations, rollback |
| `release-manager` | Coordinates changelog, smoke validation, and rollout notes. | `hermes profile install github.com/YOUR_ORG/release-manager --alias` | release, CI, smoke testing |
| `research-assistant` | Builds source-grounded briefs with uncertainty labels. | `hermes profile install github.com/YOUR_ORG/research-assistant --alias` | research, documentation |

Machine-readable metadata lives in `gallery.json`. Replace `YOUR_ORG` before publishing any install command.
