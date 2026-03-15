from __future__ import annotations

import time
from typing import Iterable

import dns.resolver
from pycdmon import CdmonDomainsClient


def _zone_from_fqdn(fqdn: str) -> str:
    parts = fqdn.rstrip(".").split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid domain: {fqdn}")
    return ".".join(parts[-2:])


def _host_from_fqdn(fqdn: str, zone: str) -> str:
    fqdn = fqdn.rstrip(".")
    suffix = f".{zone}"
    if fqdn == zone:
        return "@"
    if fqdn.endswith(suffix):
        return fqdn[: -len(suffix)]
    raise ValueError(f"FQDN {fqdn} does not belong to zone {zone}")


def create_txt_record(
    api_key: str,
    fqdn: str,
    value: str,
    ttl: int = 60,
    retries: int = 3,
) -> None:
    zone = _zone_from_fqdn(fqdn)
    host = _host_from_fqdn(fqdn, zone)
    _last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with CdmonDomainsClient(api_key=api_key) as client:
                client.create_dns_record(
                    zone,
                    {
                        "host": host,
                        "type": "TXT",
                        "ttl": ttl,
                        "destination": value,
                    },
                )
            return
        except Exception as exc:
            _last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)

    if _last_error is not None:
        raise _last_error


def delete_txt_record(api_key: str, fqdn: str, retries: int = 3) -> None:
    zone = _zone_from_fqdn(fqdn)
    host = _host_from_fqdn(fqdn, zone)

    for attempt in range(1, retries + 1):
        try:
            with CdmonDomainsClient(api_key=api_key) as client:
                client.delete_dns_record(zone, host=host, type_="TXT")
            return
        except Exception:
            if attempt < retries:
                time.sleep(attempt * 2)


def wait_for_txt(
    fqdn: str,
    expected_values: Iterable[str],
    timeout_seconds: int = 180,
    interval_seconds: int = 10,
) -> None:
    expected = {v.strip('"') for v in expected_values}
    start = time.time()

    while True:
        try:
            answers = dns.resolver.resolve(fqdn, "TXT")
            found = {"".join(s.decode() for s in rdata.strings).strip('"') for rdata in answers}
            if expected.issubset(found):
                return
        except Exception:
            pass

        if time.time() - start > timeout_seconds:
            raise TimeoutError(f"TXT propagation timeout for {fqdn}")

        time.sleep(interval_seconds)
