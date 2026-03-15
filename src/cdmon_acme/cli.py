from __future__ import annotations

import argparse
import os
from pathlib import Path

from .issuer import issue_certificate
from .models import IssueRequest

LE_PROD = "https://acme-v02.api.letsencrypt.org/directory"
LE_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cdmon-acme", description="Issue Let's Encrypt certs via cdmon DNS")
    sub = p.add_subparsers(dest="cmd", required=True)

    issue = sub.add_parser("issue", help="Issue a certificate")
    issue.add_argument("--domain", required=True)
    issue.add_argument("--email", required=True)
    issue.add_argument("--wildcard", action="store_true")
    issue.add_argument("--staging", action="store_true")
    issue.add_argument("--directory-url", default=None)
    issue.add_argument("--out", default="./certs")
    issue.add_argument("--account-key", default="./secrets/acme-account.key")
    issue.add_argument("--cert-key", default="./secrets/domain.key")
    issue.add_argument("--propagation-timeout", type=int, default=240)
    issue.add_argument("--propagation-interval", type=int, default=10)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    api_key = os.getenv("CDMON_API_KEY")
    if not api_key:
        raise SystemExit("Missing CDMON_API_KEY")

    if args.cmd == "issue":
        directory_url = args.directory_url or (LE_STAGING if args.staging else LE_PROD)
        result = issue_certificate(
            api_key=api_key,
            request=IssueRequest(
                domain=args.domain,
                wildcard=args.wildcard,
                email=args.email,
                out_dir=Path(args.out),
                directory_url=directory_url,
                account_key_path=Path(args.account_key),
                cert_key_path=Path(args.cert_key),
                propagation_timeout=args.propagation_timeout,
                propagation_interval=args.propagation_interval,
            ),
        )
        print("Issued successfully")
        print(f" cert:      {result.cert_pem_path}")
        print(f" chain:     {result.chain_pem_path}")
        print(f" fullchain: {result.fullchain_pem_path}")
        print(f" key:       {result.private_key_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
