"""Static WebRTC leak mitigation checks; real ICE/Tunnel behavior needs device tests."""
import copy
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_config import validate_profile
from verify import UniqueKeysLoader

PORTS = (3478, 3479, 5349, 5350, 19302, 19303, 19304, 19305,
         19306, 19307, 19308, 19309)
GUARDS = ["PROTOCOL,STUN,REJECT"] + [f"DST-PORT,{port},REJECT" for port in PORTS]
PROFILES = ("StashKit.yaml", "StashKit-Local.yaml", "StashKit-Privacy.yaml")


def load(name):
    return yaml.load((ROOT / name).read_text(), Loader=UniqueKeysLoader)


class WebRTCGuardTests(unittest.TestCase):
    def test_every_profile_blocks_stun_before_lan_and_domestic_bypass(self):
        for name in PROFILES:
            with self.subTest(profile=name):
                profile = load(name)
                validate_profile(profile)
                rules = profile["rules"]
                # DNS-privacy's encrypted resolver rule must remain at index zero.
                offset = 1 if name == "StashKit-Privacy.yaml" else 0
                self.assertEqual(rules[offset:offset + len(GUARDS)], GUARDS)
                self.assertLess(rules.index(GUARDS[0]),
                                rules.index("GEOIP,LAN,DIRECT,no-resolve"))
                self.assertLess(rules.index(GUARDS[0]),
                                rules.index("GEOIP,CN,DIRECT,no-resolve"))
                self.assertFalse(any("stun" in entry.lower()
                                     for entry in profile["dns"]["fake-ip-filter"]))

    def test_guard_is_validated_and_rejects_bad_protocol_or_ports(self):
        base = load("StashKit.yaml")
        for malformed in ("PROTOCOL,UNKNOWN,REJECT", "PROTOCOL,TCP,REJECT",
                          "DST-PORT,0,REJECT", "DST-PORT,65536,REJECT",
                          "DST-PORT,not-a-port,REJECT", "DST-PORT,-1,REJECT"):
            with self.subTest(malformed=malformed):
                profile = copy.deepcopy(base)
                profile["rules"][0] = malformed
                with self.assertRaises(ValueError):
                    validate_profile(profile)

    def test_no_blanket_udp_block_or_ipv6_dns_toggle_is_misrepresented(self):
        for name in PROFILES:
            with self.subTest(profile=name):
                profile = load(name)
                self.assertNotIn("NETWORK,udp,REJECT", profile["rules"])
                # Stash's DNS IPv6 switch cannot suppress native-interface ICE
                # candidates or enable IPv6 packet interception by itself.
                self.assertNotIn("ipv6", profile["dns"])


if __name__ == "__main__":
    unittest.main()
