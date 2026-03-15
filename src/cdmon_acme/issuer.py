from __future__ import annotations

from pathlib import Path
from typing import Iterable

from acme import client, challenges, messages
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from josepy import JWKRSA

from .dns_solver import create_txt_record, delete_txt_record, wait_for_txt
from .models import IssueRequest, IssuedCertificate


def _load_or_create_rsa_key(path: Path, bits: int = 4096) -> rsa.RSAPrivateKey:
    if path.exists():
        return serialization.load_pem_private_key(path.read_bytes(), password=None)

    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return key


def _generate_csr(private_key: rsa.RSAPrivateKey, domains: Iterable[str]) -> bytes:
    domain_list = list(dict.fromkeys(domains))
    if not domain_list:
        raise ValueError("At least one domain is required")

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain_list[0])]))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(d) for d in domain_list]), critical=False)
        .sign(private_key, hashes.SHA256())
    )
    return csr.public_bytes(serialization.Encoding.PEM)


def issue_certificate(api_key: str, request: IssueRequest) -> IssuedCertificate:
    account_key = _load_or_create_rsa_key(request.account_key_path)
    cert_key = _load_or_create_rsa_key(request.cert_key_path)

    jwk = JWKRSA(key=account_key)
    net = client.ClientNetwork(jwk, user_agent="cdmon-acme/0.1.0")
    directory = client.ClientV2.get_directory(request.directory_url, net)
    acme_client = client.ClientV2(directory, net)

    new_account = messages.NewRegistration.from_data(
        email=request.email,
        terms_of_service_agreed=True,
    )
    try:
        acme_client.new_account(new_account)
    except messages.Error:
        # account likely exists already for this key
        pass

    identifiers = [request.domain]
    if request.wildcard:
        identifiers.insert(0, f"*.{request.domain}")

    csr_pem = _generate_csr(cert_key, identifiers)
    order = acme_client.new_order(csr_pem)

    txt_records: list[tuple[str, str]] = []
    try:
        for authz in order.authorizations:
            identifier = authz.body.identifier.value
            dns01 = next(
                (c for c in authz.body.challenges if isinstance(c.chall, challenges.DNS01)),
                None,
            )
            if dns01 is None:
                raise RuntimeError(f"No DNS-01 challenge found for {identifier}")

            validation = dns01.validation(acme_client.net.key)
            challenge_fqdn = f"_acme-challenge.{identifier.strip('*.')}"

            create_txt_record(api_key, challenge_fqdn, validation)
            txt_records.append((challenge_fqdn, validation))

            wait_for_txt(
                challenge_fqdn,
                [validation],
                timeout_seconds=request.propagation_timeout,
                interval_seconds=request.propagation_interval,
            )

            response = dns01.response(acme_client.net.key)
            acme_client.answer_challenge(dns01, response)

        finalized_order = acme_client.poll_and_finalize(order)

    finally:
        for fqdn, _ in txt_records:
            try:
                delete_txt_record(api_key, fqdn)
            except Exception:
                pass

    request.out_dir.mkdir(parents=True, exist_ok=True)
    fullchain_path = request.out_dir / "fullchain.pem"
    cert_path = request.out_dir / "cert.pem"
    chain_path = request.out_dir / "chain.pem"

    fullchain_pem = finalized_order.fullchain_pem
    fullchain_path.write_text(fullchain_pem)

    certs = [chunk + "-----END CERTIFICATE-----\n" for chunk in fullchain_pem.split("-----END CERTIFICATE-----") if "BEGIN CERTIFICATE" in chunk]
    if certs:
        cert_path.write_text(certs[0])
        chain_path.write_text("".join(certs[1:]))

    return IssuedCertificate(
        cert_pem_path=cert_path,
        chain_pem_path=chain_path,
        fullchain_pem_path=fullchain_path,
        private_key_path=request.cert_key_path,
    )
