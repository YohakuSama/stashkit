#!/usr/bin/env python3
"""Probe the pinned encrypted DoH bootstrap and verify HTTPS certificate identity.

A DNS wire query to the literal IP must return a valid RFC8484 message over
certificate-verified HTTPS. This does not test iOS DNS leak prevention.
"""
import base64
import ipaddress
import struct
import urllib.request
import yaml
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
config = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
dns = config["dns"]
urls = set(dns["default-nameserver"] + dns["proxy-server-nameserver"])

# One A query for example.com. ID 0x3107.
query = struct.pack("!HHHHHH", 0x3107, 0x0100, 1, 0, 0, 0)
query += b"\x07example\x03com\x00" + struct.pack("!HH", 1, 1)
encoded = base64.urlsafe_b64encode(query).rstrip(b"=").decode("ascii")

for url in sorted(urls):
    parts = urlsplit(url)
    assert parts.scheme == "https" and parts.path == "/dns-query", url
    ipaddress.ip_address(parts.hostname)  # Bootstrap must not require a resolver.
    req = urllib.request.Request(
        url + "?dns=" + encoded,
        headers={"Accept": "application/dns-message", "User-Agent": "StashKit-DNS-Validation"},
    )
    # urllib verifies the server certificate, including the IP address subject.
    with urllib.request.urlopen(req, timeout=20) as response:
        wire = response.read()
        ctype = response.headers.get("Content-Type", "")
        assert response.status == 200, response.status
        assert "application/dns-message" in ctype.lower(), ctype
        assert len(wire) >= 12 and wire[:2] == b"\x31\x07", wire[:12]
        flags, qcount = struct.unpack("!HH", wire[2:6])
        assert flags & 0x8000 and qcount == 1, (flags, qcount)
    print(f"PASS: {url} RFC8484 DoH, HTTPS certificate verified, DNS response valid")
