from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class IssueRequest:
    domain: str
    wildcard: bool
    email: str
    out_dir: Path
    directory_url: str
    account_key_path: Path
    cert_key_path: Path
    propagation_timeout: int = 180
    propagation_interval: int = 10


@dataclass(slots=True)
class IssuedCertificate:
    cert_pem_path: Path
    chain_pem_path: Path
    fullchain_pem_path: Path
    private_key_path: Path
