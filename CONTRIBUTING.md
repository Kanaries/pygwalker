# Contributing to PyGWalker

New contributors (and coding agents) should start with [`AGENTS.md`](AGENTS.md): it maps the
repo, explains how the Python and frontend halves are built, and documents the one-command dev
stack (`python scripts/dev.py`) with live frontend reload and centralized logs.

The detailed contributor workflow lives in [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md),
covering:

- Python editable installs and test commands.
- Frontend dependency installation, builds, type checks, and Playwright smoke tests.
- Optional local Graphic Walker source builds through `app`'s `dev:preinstall` script.
- The hot-reload dev workflow ([`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)) and project
  architecture ([`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)).
- CI and package-build expectations.

Keeping the detailed guide under `docs/` lets the development notes and
troubleshooting page link to one maintained source of truth.
