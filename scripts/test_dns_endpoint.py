#!/usr/bin/env python3
"""Probe IP-literal DoH with TLS identity and complete DNS response validation.

Importing this module performs no network requests. This is not an iOS DNS-leak
test. The default HTTPS context verifies both the CA chain and the IP identity.
"""
import base64
import ipaddress
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

import dns.exception
import dns.flags
import dns.message
import dns.opcode
import dns.rcode
import dns.rdatatype
import yaml


def make_query():
    query = dns.message.make_query("example.com.", dns.rdatatype.A)
    query.id = 0x3107
    return query


def validate_dns_response(wire, query):
    """Require a complete, successful answer to this exact question."""
    if not 12 <= len(wire) <= 65535:
        raise ValueError("Invalid DNS message length")
    try:
        response = dns.message.from_wire(wire, raise_on_truncation=True)
        if not response.flags & dns.flags.QR or response.opcode() != dns.opcode.QUERY:
            raise ValueError("Expected a standard DNS response")
        if response.id != query.id:
            raise ValueError("DNS transaction ID mismatch")
        if response.rcode() != dns.rcode.NOERROR:
            raise ValueError(f"DNS query failed: {dns.rcode.to_text(response.rcode())}")
        if len(response.question) != 1 or response.question != query.question:
            raise ValueError("DNS question mismatch")
        # An unrelated A record is not an answer to this query.
        answer = response.resolve_chaining().answer
        if answer is None or answer.rdtype != dns.rdatatype.A or not len(answer):
            raise ValueError("DNS response has no final A answer")
        addresses = [record.address for record in answer]
        if not all(ipaddress.ip_address(value).is_global for value in addresses):
            raise ValueError("example.com returned a non-public address")
        return addresses
    except dns.exception.DNSException as error:
        raise ValueError(f"Malformed or truncated DNS response: {error}") from error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "DoH redirects are not accepted", headers, fp)


def probe_endpoint(url, opener=None):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.path != "/dns-query" or parts.query
            or parts.fragment or parts.username or parts.password):
        raise ValueError(f"Expected an HTTPS bootstrap /dns-query endpoint: {url}")
    ipaddress.ip_address(parts.hostname)
    query = make_query()
    encoded = base64.urlsafe_b64encode(query.to_wire()).rstrip(b"=").decode("ascii")
    req = urllib.request.Request(
        url + "?dns=" + encoded,
        headers={"Accept": "application/dns-message", "User-Agent": "StashKit-DNS-Validation"},
    )
    if opener is None:
        opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    with opener.open(req, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"Unexpected HTTP status: {response.status}")
        ctype = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if ctype != "application/dns-message":
            raise ValueError(f"Unexpected DoH content type: {ctype}")
        wire = response.read(65536)
    return validate_dns_response(wire, query)


def main():
    root = Path(__file__).resolve().parents[1]
    settings = yaml.safe_load((root / "StashKit.yaml").read_text(encoding="utf-8"))["dns"]
    urls = set(settings["default-nameserver"] + settings["proxy-server-nameserver"])
    for url in sorted(urls):
        addresses = probe_endpoint(url)
        print(f"PASS: {url} HTTPS certificate identity verified; complete NOERROR DNS A answer: {addresses}")


if __name__ == "__main__":
    main()
