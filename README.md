# drawflow-engine

Windows desktop application that automates a façade draftsman's tasks:

- **Parts list**: DWG/DXF drawings → Excel list of parts and quantities.
- **Report**: PDF drawings → Word report (title block, references).
- **Submission**: XLSX submissions, or PDF with an embedded XLSX → normalized table.

It also ships a **local assistant** (AI model running on the workstation, nothing leaves the machine), a **Setup screen** that installs the prerequisites in one click, **presets**, and control from a **Stream Dock** (Mirabox).

Stack: Tauri 2 · React + TypeScript · Python engine (PyInstaller sidecar).

The application and its user guide are available in French and English; the developer documentation is in French.

## Documentation

| Document | Audience | Content |
|---|---|---|
| [User guide](docs/guide.md) (FR) · [English](docs/guide.en.md) | Users | Install, use each feature, assistant, Stream Dock, troubleshooting |
| [Architecture](docs/architecture.md) (FR) | Developers | Overview, main flows, decisions and their reasons, CI/CD |
| [Local API](docs/api-locale.md) (FR) | Integrations | WebSocket protocol (Stream Dock, third-party tools) |
| [Changelog](CHANGELOG.md) (FR) | Everyone | Content of each version |
| [CLAUDE.md](CLAUDE.md) (FR) | Developers | Development rules and commands |

Documentation rules:

1. One file per audience, and each piece of information in a single place; elsewhere, a link.
2. No values the code already knows (defaults, field lists, versions): point to the application or the code.
3. The why rather than the what: every structuring choice goes to "Décisions" in the architecture document (one line, the reason, the PR).
4. Maximum size: README ~80 lines, guide and architecture ~300 lines each. Beyond that, cut; a new file only for a new audience or an external contract.
5. Updated in the PR that changes the behavior: `CHANGELOG.md` always, the other documents when affected.

## Development

Prerequisites: Node 22 + pnpm, Python 3.12 + uv, Rust stable.

```bash
pnpm install
(cd engine && uv sync)
pnpm dev            # builds the sidecar, then starts the application
```

Tests and checks: see the "Commandes" section of [CLAUDE.md](CLAUDE.md). In development, the access code and the updater are disabled.

## Releasing

1. In `CHANGELOG.md`, move the `## Non publié` entries under a new `## X.Y.Z — YYYY-MM-DD` heading, then `pnpm version:bump X.Y.Z` (UI, Tauri, Rust, engine, Stream Dock plugin); commit through a PR.
2. Once merged: `git tag vX.Y.Z && git push origin vX.Y.Z`. The workflow first runs `pnpm version:check -- --tag vX.Y.Z`: versions aligned with the tag, changelog section present, `## Non publié` empty.
3. The `Release` workflow builds the Windows installer (NSIS), creates a draft release whose notes are that changelog section (also carried by the signed `latest.json`), attaches the Stream Dock plugin `ch.drawflow.sdPlugin.zip`, then publishes the release.

One-time prerequisites:
- `pnpm tauri signer generate -w ~/.tauri/drawflow.key`, with a password (the workflow refuses an empty one), then the secrets `TAURI_SIGNING_PRIVATE_KEY` (file content) and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`, and the variable `UPDATER_PUBKEY` (public key).
- To publish releases in another public repository: variables `RELEASES_OWNER` and `RELEASES_REPO`, secret `RELEASES_TOKEN` (`contents:write` on that repository).

The update endpoint (`releases/latest/download/latest.json`) ignores pre-releases.
