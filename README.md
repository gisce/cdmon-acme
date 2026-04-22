# cdmon-acme

Issue Let's Encrypt certificates (including wildcard) using cdmon DNS (`dns-01`) via `pycdmon`.

## Features

- Wildcard support (`*.example.com`)
- Fully Python implementation
- DNS TXT automation on cdmon
- DNS propagation wait loop
- Retries/backoff for DNS record create/delete
- Lock file to prevent parallel issuance
- Commands: `issue`, `renew`, `inspect`
- Outputs: `cert.pem`, `chain.pem`, `fullchain.pem`, private key

## Install

```bash
pip install -e .
```

## Usage

```bash
export CDMON_API_KEY="..."

# Staging first (recommended)
cdmon-acme issue \
  --domain example.com \
  --wildcard \
  --email admin@example.com \
  --staging \
  --out ./certs

# Production
cdmon-acme issue \
  --domain example.com \
  --wildcard \
  --email admin@example.com \
  --out ./certs

# Renew (same flow, reusable keys + lock)
cdmon-acme renew \
  --domain example.com \
  --wildcard \
  --email admin@example.com \
  --out ./certs \
  --lock-file ./.state/issue.lock \
  --post-hook "systemctl reload nginx"

# Inspect existing cert
cdmon-acme inspect --cert ./certs/fullchain.pem
```

## Security notes

- Never commit private keys (`secrets/`, `certs/`)
- Rotate/revoke credentials if exposed
- Use staging first to avoid Let's Encrypt rate limits

## Repo structure

- `src/cdmon_acme/issuer.py` ACME + issuance flow
- `src/cdmon_acme/dns_solver.py` cdmon DNS TXT create/delete + propagation
- `src/cdmon_acme/cert_info.py` certificate inspection helpers
- `src/cdmon_acme/cli.py` CLI

## GitHub Actions renew example

Add repository secrets:
- `CDMON_API_KEY`
- `ACME_EMAIL`

Then use a scheduled workflow (example in `.github/workflows/renew-example.yml`).

## Releases

This repository supports automatic releases from `main` using **Python Semantic Release** and Conventional Commits.

### Why this approach

This is a Python package, so the release automation is Python-native:

- no `package.json`
- versioning is configured in `pyproject.toml`
- the workflow uses `python-semantic-release`, `build`, and optional PyPI publication

Conventional Commits are only the input convention used to determine the version bump.

### How it works

- merge changes into `main`
- GitHub Actions runs validation (`ruff check .` and `pytest`)
- `python-semantic-release` inspects commit messages since the last tag
- if a release is warranted, it will:
  - determine the next version
  - update `pyproject.toml`
  - create the release commit and tag
  - publish the GitHub Release
- if `PYPI_TOKEN` is defined in repository secrets, the workflow also publishes to PyPI
- if `PYPI_TOKEN` is not defined but `PYPI_MASTER_TOKEN` exists, the workflow falls back to that token for PyPI publication
- if neither token exists, the workflow still creates the Git tag and GitHub Release and skips the PyPI upload

### Commit conventions

Use Conventional Commits so release automation can infer version bumps:

- `fix:` -> patch release
- `feat:` -> minor release
- `feat!:` or any commit with `BREAKING CHANGE:` -> major release
- `docs:`, `test:`, `chore:` -> no release by default

Example:

```bash
git commit -m "fix: correct TXT record handling for cdmon DNS challenge"
```

### Notes

- The release workflow only runs on pushes to `main`.
- The repository must allow GitHub Actions to push release commits and tags using `GITHUB_TOKEN`.
- If branch protection is strict, make sure it still permits the release workflow to push the generated release commit.

## Status

MVP+ ready. Next recommended steps:

- Add integration tests against LE staging + disposable domain
- Add deploy target adapters (nginx/caddy/traefik)
- Add optional webhook/slack notification on renew
