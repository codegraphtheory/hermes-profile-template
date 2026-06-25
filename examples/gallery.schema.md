# Examples Gallery Schema

`examples/gallery.json` is machine-readable metadata for curated generated profile examples. It is meant for repository browsing, docs rendering, and discovery tooling. It is not an install manifest.

## Schema

- `schema_version`: Stable schema identifier. Current value: `hermes-profile-examples/v0.1`.
- `schema_docs`: Repository-relative path to this schema description.
- `examples`: Array of example profile records.

Each example record includes:

- `name`: Kebab-case example name.
- `path`: Repository-relative path to the generated example profile.
- `use_case`: One-sentence description of the profile's job.
- `template`: `true` when install commands still contain publication placeholders.
- `publish_hint`: Human-readable note for replacing placeholders before sharing install commands.
- `install_command`: Example Hermes install command.
- `validation_command`: Command maintainers can run from the repository root.
- `keywords`: Domain and discovery terms used by the example README.

## Placeholder Policy

Install commands that include `github.com/YOUR_ORG/...` are templates, not tested live repositories. Downstream renderers should display `publish_hint` with those commands and should not treat them as live install targets until the owner placeholder is replaced.
