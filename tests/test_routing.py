"""Offline routing sentinels, not a replacement for Stash's /rules/match.

Only explicit domain rules, inline private rules, text providers and private IPs
are modelled. Public GeoIP/ASN data and DNS resolution require Stash.
"""
import ipaddress
import re
import sys
import unittest
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import UniqueKeysLoader

LAN_NETWORKS = tuple(map(ipaddress.ip_network, (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8",
    "169.254.0.0/16", "::1/128", "fc00::/7", "fe80::/10",
)))


@lru_cache(maxsize=None)
def provider_entries(filename):
    path = ROOT / "rules" / filename
    if filename == "Crypto.v7.0.13.domain.txt":
        path = ROOT / "rules/extra/Crypto.v7.0.13.domain.txt"
    return frozenset(row.strip() for row in path.read_text().splitlines()
                     if row.strip() and not row.lstrip().startswith("#"))


def route(target, profile):
    """Return the first statically decidable policy for a sentinel target."""
    target = target.lower().rstrip(".")
    try:
        address = ipaddress.ip_address(target)
    except ValueError:
        address = None
    labels = target.lower().rstrip(".").split(".")
    suffixes = {".".join(labels[i:]) for i in range(len(labels))}
    for rule in profile["rules"]:
        kind, *args = rule.split(",")
        if kind == "MATCH":
            return args[0]
        value, policy = args[:2]
        if kind == "DOMAIN" and target == value:
            return policy
        if kind == "DOMAIN-SUFFIX" and value in suffixes:
            return policy
        if kind == "GEOIP" and value == "LAN" and address is not None:
            if any(address.version == net.version and address in net for net in LAN_NETWORKS):
                return policy
        if kind == "RULE-SET":
            spec = profile["rule-providers"][value]
            entries = spec["payload"] if spec.get("type") == "inline" else provider_entries(
                spec.get("url", spec.get("path")).rsplit("/", 1)[1])
            if spec["behavior"] == "classical" and address is None:
                for row in entries:
                    matcher, value, *_ = row.split(",")
                    if ((matcher == "DOMAIN" and target == value) or
                        (matcher == "DOMAIN-SUFFIX" and value in suffixes) or
                        (matcher == "DOMAIN-REGEX" and re.search(value, target))):
                        return policy
            if spec["behavior"] == "domain" and address is None:
                if target in entries or any("+." + suffix in entries for suffix in suffixes):
                    return policy
            if spec["behavior"] == "ipcidr" and address is not None:
                if any(address.version == net.version and address in net
                       for net in map(ipaddress.ip_network, entries)):
                    return policy
    raise AssertionError("No MATCH rule")


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = yaml.load((ROOT / "StashKit.yaml").read_text(), Loader=UniqueKeysLoader)

    def test_private_targets_are_direct(self):
        for target in ("localhost", "nas.local", "router.lan", "printer.home.arpa",
                       "192.168.1.1", "10.0.0.1", "172.16.1.1", "169.254.1.1",
                       "127.0.0.1", "::1", "fd00::1", "fe80::1"):
            with self.subTest(target=target):
                self.assertEqual(route(target, self.profile), "DIRECT")

    def test_private_dns_is_scoped_to_system(self):
        dns = self.profile["dns"]
        for name in ("rule-set:Private-local", "+.local", "+.lan", "+.home.arpa"):
            self.assertEqual(dns["nameserver-policy"][name], "system")
            self.assertIn(name, dns["fake-ip-filter"])
        self.assertEqual(dns["nameserver"], ["https://dns.alidns.com/dns-query"])

    def test_public_service_routes_stay_separate(self):
        for target, policy in (("api.openai.com", "ChatGPT"),
                               ("gemini.google.com", "Gemini"),
                               ("raw.githubusercontent.com", "GitHub"),
                               ("example.com", "Final")):
            with self.subTest(target=target):
                self.assertEqual(route(target, self.profile), policy)

    def test_advertising_overrides_earlier_service_and_cn_collections(self):
        # Overlap is intentional: early AdBlock rules must not be shadowed by
        # broad service or ChinaDirect suffixes.
        expected = {
            "0ka.com": "AdBlock",
            "analytics.msnbc.msn.com": "AdBlock",
            "collector.github.com": "AdBlock",
        }
        for target, policy in expected.items():
            with self.subTest(target=target):
                self.assertEqual(route(target, self.profile), policy)

    def test_google_ads_and_copilot_telemetry_are_blocked_in_every_profile(self):
        targets = ("googleads.g.doubleclick.net", "pagead2.googlesyndication.com",
                   "www.googleadservices.com", "www.google-analytics.com",
                   "www.doubleclick-cn.net", "www.googlesyndication-cn.com",
                   "www.googleadservices-cn.com", "www.google-analytics-cn.com",
                   "copilot-telemetry.githubusercontent.com")
        for name in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.load((ROOT / name).read_text(), Loader=UniqueKeysLoader)
            for target in targets:
                with self.subTest(profile=name, target=target):
                    self.assertEqual(route(target, profile), "AdBlock")
            for target, policy in (("www.google.com", "Google"), ("accounts.google.com", "Google"),
                                   ("copilot-proxy.githubusercontent.com", "AI")):
                self.assertEqual(route(target, profile), policy)

    def test_private_names_work_without_geosite_downloads(self):
        for name in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.load((ROOT / name).read_text(), Loader=UniqueKeysLoader)
            self.assertNotIn("GEOSITE,private,DIRECT", profile["rules"])
            for target in ("nas", "router.internal", "host.localdomain", "router.asus.com",
                           "host.ts.net", "1.168.192.in-addr.arpa", "localhost.weixin.qq.com"):
                with self.subTest(profile=name, target=target):
                    self.assertEqual(route(target, profile), "DIRECT")

    def test_streaming_cdn_exceptions_are_scoped(self):
        expected = {
            "www.digicert.com": "Final",
            "www.hinet.net": "Final",
            "gamer-cds.cdn.hinet.net": "動畫瘋",
            "gamer2-cds.cdn.hinet.net": "動畫瘋",
            "alibaba.cdn.steampipe.steamcontent.com": "DIRECT",
            "other.steamcontent.com": "Steam",
            "control.kochava.com": "AdBlock",
            "graph.facebook.com": "Whatsapp",
            "www.amazon.com": "PrimeVideo",
            "redirector.gvt1.com": "YouTube",
            "api.statsig.com": "Proxy",
            "challenges.cloudflare.com": "Cloudflare",
        }
        for target, policy in expected.items():
            with self.subTest(target=target):
                self.assertEqual(route(target, self.profile), policy)


    def test_loonkit_v7016_apple_pcc_stripe_split_with_existing_providers(self):
        checks = {
            "guzzoni.apple.com": "Apple",
            "search.smoot.apple.com": "Apple",
            "apple-relay.apple.com": "Apple",
            "apple-relay.cloudflare.com": "Apple",
            "apple-relay.fastly-edge.com": "Apple",
            "cp4.cloudflare.com": "Apple",
            "api.cloudflare.com": "Cloudflare",
            "challenges.cloudflare.com": "Cloudflare",
            "stripe.com": "Proxy",
            "api.stripe.com": "Proxy",
            "m.stripe.network": "Proxy",
            "api.openai.com": "ChatGPT",
            "gemini.google.com": "Gemini",
            "quark.cn": "DIRECT",
            "www.youtube.com": "YouTube",
            "notstripe.com": "Final",
            "cloudflare.com.example.invalid": "Final",
            "unknown-stashkit.example.invalid": "Final",
        }
        for filename in ("StashKit.yaml", "StashKit-Subscription.yaml",
                         "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.load((ROOT / filename).read_text(), Loader=UniqueKeysLoader)
            groups = profile["proxy-groups"]
            self.assertEqual(len(groups), 40)
            providers = profile["rule-providers"]
            self.assertEqual(len(providers), 56)
            self.assertEqual(providers["Apple-domain"]["behavior"], "domain")
            self.assertEqual(providers["SharedInfrastructure-domain"]["behavior"], "domain")
            rules = profile["rules"]
            self.assertLess(rules.index("RULE-SET,AppleOTA-domain,Apple"),
                            rules.index("RULE-SET,Apple-domain,Apple"))
            self.assertLess(rules.index("RULE-SET,Apple-domain,Apple"),
                            rules.index("RULE-SET,Cloudflare-domain,Cloudflare"))
            self.assertEqual(rules[-2:], ["GEOIP,CN,DIRECT,no-resolve", "MATCH,Final"])
            for host, wanted in checks.items():
                with self.subTest(profile=filename, host=host):
                    self.assertEqual(route(host, profile), wanted)
            self.assertFalse(any(rule.startswith(("DOMAIN,apple-relay.", "DOMAIN,cp4.",
                                                    "DOMAIN-SUFFIX,stripe."))
                                 for rule in rules))

    def test_loonkit_v7015_sites_use_existing_remote_categories(self):
        international = (
            "duolingo.com", "mediawiki.org", "w.wiki", "wikibooks.org",
            "wikidata.org", "wikimedia.org", "wikimediafoundation.org",
            "wikinews.org", "wikipedia.org", "wikiquote.org",
            "wikisource.org", "wikiversity.org", "wikivoyage.org",
            "wiktionary.org", "wmfusercontent.org",
        )
        for name in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.load((ROOT / name).read_text(), Loader=UniqueKeysLoader)
            self.assertEqual(len(profile["rule-providers"]), 56)  # 55 remote + Private-local inline
            self.assertEqual(len(profile["proxy-groups"]), 40)
            self.assertFalse(any("QuarkDirect" in key or "WikipediaDuolingo" in key
                                 for key in profile["rule-providers"]))
            for host in ("quark.cn", "www.quark.cn", "pan.myquark.cn"):
                with self.subTest(profile=name, host=host):
                    self.assertEqual(route(host, profile), "DIRECT")
            for root in international:
                for host in (root, "www." + root):
                    with self.subTest(profile=name, host=host):
                        self.assertEqual(route(host, profile), "Proxy")
            for host in ("notquark.cn",
                         "notduolingo.com", "wikipedia.org.unrelated.example"):
                with self.subTest(profile=name, host=host):
                    self.assertNotEqual(route(host, profile),
                                        "DIRECT" if "quark" in host else "Proxy")
            self.assertNotEqual(route("duolingo.cn", profile), "Proxy")

    def test_crypto_routes_take_priority_over_domestic_and_fallback(self):
        exact = (
            "binance.com", "api.binance.com", "www.okx.com", "www.bybit.com",
            "api.coinbase.com", "www.kraken.com", "wallet.metamask.io",
            "www.coingecko.com", "api.gemini.com", "api.crypto.com",
            "scan.etherscan.io", "www.dexscreener.com",
            "coincheck.com", "trade.coincheck.com", "app.hyperliquid.xyz",
            "wallet.phantom.app", "app.aave.com", "solscan.io",
            "app.pancakeswap.finance",
        )
        unrelated = ("notbinance.com", "binance.com.example.net",
                     "crypto.example.net", "notcoincheck.com")
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.load((ROOT / filename).read_text(), Loader=UniqueKeysLoader)
            for target in exact:
                with self.subTest(filename=filename, target=target):
                    self.assertEqual(route(target, profile), "Crypto")
            rules = profile["rules"]
            self.assertLess(rules.index("DOMAIN,coincheck.com,Crypto"),
                            rules.index("RULE-SET,AdBlockBalanced-domain,AdBlock"))
            self.assertLess(rules.index("RULE-SET,AdBlockBalanced-domain,AdBlock"),
                            rules.index("RULE-SET,Crypto-domain,Crypto"))
            for target in unrelated:
                with self.subTest(filename=filename, unrelated=target):
                    self.assertNotEqual(route(target, profile), "Crypto")


if __name__ == "__main__":
    unittest.main()
