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

## Status

MVP+ ready. Next recommended steps:

- Add integration tests against LE staging + disposable domain
- Add deploy target adapters (nginx/caddy/traefik)
- Add optional webhook/slack notification on renew
