# cdmon-acme

Issue Let's Encrypt certificates (including wildcard) using cdmon DNS (`dns-01`) via `pycdmon`.

## Features

- Wildcard support (`*.example.com`)
- Fully Python implementation
- DNS TXT automation on cdmon
- DNS propagation wait loop
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
```

## Security notes

- Never commit private keys (`secrets/`, `certs/`)
- Rotate/revoke credentials if exposed
- Use staging first to avoid Let's Encrypt rate limits

## Repo structure

- `src/cdmon_acme/issuer.py` ACME + issuance flow
- `src/cdmon_acme/dns_solver.py` cdmon DNS TXT create/delete + propagation
- `src/cdmon_acme/cli.py` CLI

## Status

MVP ready. Next recommended steps:

- Add renew subcommand
- Add lockfile to prevent parallel issuance
- Add integration tests against LE staging + disposable domain
