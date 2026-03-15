from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from pathlib import Path

from .cert_info import inspect_certificate
from .issuer import issue_certificate
from .models import IssueRequest

LE_PROD = "https://acme-v02.api.letsencrypt.org/directory"
LE_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"


def _add_common_issue_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--domain", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--wildcard", action="store_true")
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--directory-url", default=None)
    parser.add_argument("--out", default="./certs")
    parser.add_argument("--account-key", default="./secrets/acme-account.key")
    parser.add_argument("--cert-key", default="./secrets/domain.key")
    parser.add_argument("--lock-file", default="./.state/issue.lock")
    parser.add_argument("--propagation-timeout", type=int, default=240)
    parser.add_argument("--propagation-interval", type=int, default=10)
    parser.add_argument(
        "--post-hook",
        default=None,
        help="Optional shell command to run after successful issue/renew (e.g. 'systemctl reload nginx')",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cdmon-acme", description="Issue Let's Encrypt certs via cdmon DNS")
    sub = p.add_subparsers(dest="cmd", required=True)

    issue = sub.add_parser("issue", help="Issue a certificate")
    _add_common_issue_args(issue)

    renew = sub.add_parser("renew", help="Renew a certificate (same flow as issue)")
    _add_common_issue_args(renew)

    inspect = sub.add_parser("inspect", help="Inspect an existing certificate PEM")
    inspect.add_argument("--cert", default="./certs/fullchain.pem")

    return p


def _run_post_hook(command: str) -> None:
    subprocess.run(command, shell=True, check=True)


def _run_issue_like(args: argparse.Namespace, api_key: str) -> int:
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
            lock_path=Path(args.lock_file),
            propagation_timeout=args.propagation_timeout,
            propagation_interval=args.propagation_interval,
        ),
    )
    print("Issued successfully")
    print(f" cert:      {result.cert_pem_path}")
    print(f" chain:     {result.chain_pem_path}")
    print(f" fullchain: {result.fullchain_pem_path}")
    print(f" key:       {result.private_key_path}")

    if args.post_hook:
        print(f"Running post-hook: {shlex.quote(args.post_hook)}")
        _run_post_hook(args.post_hook)

    return 0


def _run_inspect(args: argparse.Namespace) -> int:
    info = inspect_certificate(Path(args.cert))
    print(f"subject:    {info.subject}")
    print(f"issuer:     {info.issuer}")
    print(f"not_before: {info.not_before.isoformat()}")
    print(f"not_after:  {info.not_after.isoformat()}")
    print(f"days_left:  {info.days_left}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "inspect":
        return _run_inspect(args)

    api_key = os.getenv("CDMON_API_KEY")
    if not api_key:
        raise SystemExit("Missing CDMON_API_KEY")

    if args.cmd in {"issue", "renew"}:
        return _run_issue_like(args, api_key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
