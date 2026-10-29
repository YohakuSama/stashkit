"""Regression tests for provider-aware Stash policy groups matching LoonKit behavior."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_loon_selection import (NODE_POOLS, PROFILE_FILES, NATIVE_PROFILE_FILES, build_loon_selection,
                                  read_provider_override, read_node_sources, read_subscription_urls)
from validate_config import validate_profile

PROVIDERS = {
    "personal": {
        "url": "https://example.org/node-provider.yaml",
        "interval": 3600,
        "benchmark-url": "http://www.bing.com",
        "benchmark-timeout": 5,
    },
    "backup": {
        "url": "https://example.org/backup-provider.yaml",
        "interval": 3600,
    },
}


class LoonSelectionTests(unittest.TestCase):
    def test_provider_groups_preserve_policies_and_allow_direct_node_selection(self):
        for profile_name in PROFILE_FILES.values():
            with self.subTest(profile=profile_name):
                original = yaml.safe_load((ROOT / profile_name).read_text(encoding="utf-8"))
                snapshot = copy.deepcopy(original)
                generated = build_loon_selection(original, PROVIDERS)
                validate_profile(generated)
                self.assertEqual(original, snapshot)
                for key in ("dns", "rules", "rule-providers", "mode", "log-level"):
                    self.assertEqual(generated[key], original[key])
                self.assertEqual(generated["proxy-providers"], PROVIDERS)
                by_name = {row["name"]: row for row in generated["proxy-groups"]}
                self.assertEqual(len(by_name), 40)
                self.assertIn("ALL", by_name)
                self.assertEqual(by_name["Proxy"]["proxies"],
                                 ["Auto", "Fallback", "ALL", "REJECT"])
                self.assertEqual(by_name["Auto"]["proxies"], ["REJECT"])
                self.assertEqual(by_name["Fallback"]["proxies"], ["REJECT"])
                self.assertEqual(by_name["ALL"]["proxies"], ["REJECT"])
                for name, group in by_name.items():
                    self.assertNotIn("include-all", group)
                    if name in {"Auto", "Fallback", "ALL"}:
                        self.assertEqual(group["use"], list(PROVIDERS))
                    else:
                        self.assertNotIn("use", group)
                    if name not in NODE_POOLS | {"AdBlock", "Final"}:
                        self.assertTrue({"Proxy", "Auto", "Fallback", "ALL"} <= set(group["proxies"]))
                self.assertEqual(by_name["ChatGPT"]["proxies"],
                                 ["Proxy", "Auto", "Fallback", "ALL"])

    def test_direct_service_choices_survive_all_private_node_sources(self):
        # LoonKit intentionally allows DIRECT for selected services, not for
        # every overseas AI / streaming service or for the global Proxy.
        direct_first = ("Microsoft", "Apple", "Speedtest", "Bilibili", "Line")
        direct_optional = "Steam"
        local_node = {"name": "Test Node", "type": "ss",
                      "server": "198.51.100.10", "port": 443,
                      "cipher": "aes-128-gcm", "password": "test-only"}
        sources = (
            ("providers", {"providers": PROVIDERS}),
            ("local", {"nodes": [local_node]}),
            ("use-url", {"subscription_urls": ["https://example.org/sub"]}),
        )
        for profile_name in PROFILE_FILES.values():
            source = yaml.safe_load((ROOT / profile_name).read_text(encoding="utf-8"))
            for source_type, options in sources:
                with self.subTest(profile=profile_name, source=source_type):
                    result = build_loon_selection(source, **options)
                    groups = {group["name"]: group for group in result["proxy-groups"]}
                    self.assertEqual(result["rules"], source["rules"])
                    self.assertEqual(groups["Proxy"]["proxies"][0:2],
                                     ["Auto", "Fallback"])
                    self.assertEqual(groups["Proxy"]["proxies"][-1], "REJECT")
                    self.assertNotIn("DIRECT", groups["Proxy"]["proxies"])
                    for name in direct_first:
                        self.assertEqual(groups[name]["proxies"][0:4],
                                         ["DIRECT", "Proxy", "Auto", "Fallback"])
                    self.assertEqual(groups[direct_optional]["proxies"][0:4],
                                     ["Proxy", "Auto", "Fallback", "DIRECT"])
                    for name in ("AI", "ChatGPT", "Gemini", "Claude", "Netflix"):
                        self.assertNotIn("DIRECT", groups[name]["proxies"])

    def test_missing_and_conflicting_providers_fail(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "Named nodes or providers"):
            build_loon_selection(source, {})
        with self.assertRaisesRegex(ValueError, "conflict"):
            build_loon_selection(source, {"Proxy": PROVIDERS["personal"]})
        malformed = copy.deepcopy(source)
        malformed["proxy-groups"] = malformed["proxy-groups"][1:]
        with self.assertRaisesRegex(ValueError, "Unexpected canonical"):
            build_loon_selection(malformed, PROVIDERS)

    def test_provider_override_validates_user_input_and_never_accepts_example(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "providers.stoverride"
            path.write_text(yaml.safe_dump({
                "name": "Personal node providers",
                "proxy-providers": PROVIDERS,
            }), encoding="utf-8")
            self.assertEqual(read_provider_override(path), PROVIDERS)
            path.write_text(yaml.safe_dump({
                "proxy-providers": {"personal": {
                    "url": "https://example.invalid/REPLACE-WITH-YOUR-SUBSCRIPTION",
                }},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Replace placeholder"):
                read_provider_override(path)
            path.write_text(yaml.safe_dump({
                "proxy-providers": PROVIDERS,
                "rules": ["MATCH,DIRECT"],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Expected an override"):
                read_provider_override(path)

    def test_public_preview_requires_personal_provider_and_matches_generator(self):
        preview = yaml.safe_load((ROOT / "StashKit-Loon-Preview.yaml").read_text(encoding="utf-8"))
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        expected = build_loon_selection(source, {"personal": PROVIDERS["personal"]})
        self.assertNotIn("proxy-providers", preview)
        self.assertEqual(preview["proxy-groups"], expected["proxy-groups"])
        for key in ("dns", "rules", "rule-providers", "mode", "log-level"):
            self.assertEqual(preview[key], source[key])
        preview["proxy-providers"] = {"personal": PROVIDERS["personal"]}
        validate_profile(preview)

    def test_discover_local_nodes_without_provider_name(self):
        nodes = [
            {"name": "US-LAX | Snell v6", "type": "snell", "server": "198.51.100.10", "port": 443},
            {"name": "US-LAX | HY2 Gecko", "type": "hysteria2", "server": "198.51.100.11", "port": 443},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing-subscription.yaml"
            path.write_text(yaml.safe_dump({"proxies": nodes, "proxy-groups": [
                {"name": "Provider-specific", "type": "select",
                 "proxies": [node["name"] for node in nodes]},
            ]}), encoding="utf-8")
            discovered_nodes, discovered_providers = read_node_sources(path)
            self.assertEqual(discovered_nodes, nodes)
            self.assertEqual(discovered_providers, {})
            for name in PROFILE_FILES.values():
                with self.subTest(profile=name):
                    original = yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))
                    result = build_loon_selection(original, discovered_providers, discovered_nodes)
                    validate_profile(result)
                    groups = {group["name"]: group for group in result["proxy-groups"]}
                    self.assertEqual(groups["Proxy"]["proxies"],
                                     ["Auto", "Fallback", "ALL", "REJECT"])
                    self.assertEqual(groups["ChatGPT"]["proxies"],
                                     ["Proxy", "Auto", "Fallback", "ALL"])
                    self.assertEqual(groups["Auto"]["proxies"],
                                     [node["name"] for node in nodes] + ["REJECT"])
                    self.assertEqual(groups["Fallback"]["proxies"],
                                     [node["name"] for node in nodes] + ["REJECT"])
                    self.assertEqual(groups["ALL"]["proxies"],
                                     [node["name"] for node in nodes] + ["REJECT"])
                    self.assertNotIn("include-all", groups["ChatGPT"])
                    self.assertNotIn("use", groups["ChatGPT"])
                    self.assertEqual(result["proxies"], nodes)
                    self.assertEqual(original["dns"], result["dns"])
                    self.assertEqual(original["rules"], result["rules"])

    def test_discover_names_of_multiple_providers_automatically(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "providers.yaml"
            path.write_text(yaml.safe_dump({"proxy-providers": PROVIDERS}), encoding="utf-8")
            nodes, providers = read_node_sources(path)
            self.assertEqual(nodes, [])
            self.assertEqual(providers, PROVIDERS)
            built = build_loon_selection(source, providers, nodes)
            groups = {row["name"]: row for row in built["proxy-groups"]}
            self.assertNotIn("use", groups["Proxy"])
            self.assertNotIn("use", groups["ChatGPT"])
            self.assertEqual(groups["ALL"]["use"], list(providers))

    def test_unknown_or_conflicting_node_name_rejected(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        reserved = {"name": "Auto", "type": "snell"}
        with self.assertRaisesRegex(ValueError, "conflict"):
            build_loon_selection(source, {}, [reserved])
        identical = {"name": "Node", "type": "snell"}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_loon_selection(source, {}, [identical, identical])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text(yaml.safe_dump({"proxies": [{"type": "snell"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonempty name"):
                read_node_sources(path)

    def test_native_use_url_has_same_level_policy_and_dynamic_nodes_without_names(self):
        # Two synthetic HTTPS provider endpoints. Credentials never go into public profiles.
        urls = [
            "https://example.org/clash/sub?token=redacted-1",
            "https://example.org/clash/backup?token=redacted-2",
        ]
        for filename in PROFILE_FILES.values():
            with self.subTest(profile=filename):
                original = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
                snapshot = copy.deepcopy(original)
                output = build_loon_selection(original, subscription_urls=urls)
                validate_profile(output)
                self.assertEqual(original, snapshot)
                self.assertEqual(len(output["proxy-groups"]), 40)
                groups = {g["name"]: g for g in output["proxy-groups"]}
                self.assertNotIn("Manual", groups)
                self.assertIn("ALL", groups)
                self.assertEqual(groups["Proxy"]["proxies"],
                                 ["Auto", "Fallback", "ALL", "REJECT"])
                self.assertEqual(groups["ChatGPT"]["proxies"],
                                 ["Proxy", "Auto", "Fallback", "ALL"])
                for name, group in groups.items():
                    self.assertNotIn("include-all", group)
                    self.assertNotIn("filter", group)
                    self.assertNotIn("use", group)
                    if name in {"Auto", "Fallback", "ALL"}:
                        self.assertEqual(group["use-url"], urls)
                    else:
                        self.assertNotIn("use-url", group)
                self.assertEqual(groups["Auto"]["proxies"], ["REJECT"])
                self.assertEqual(groups["Fallback"]["proxies"], ["REJECT"])
                self.assertEqual(groups["ALL"]["proxies"], ["REJECT"])
                self.assertNotIn("proxy-providers", output)
                self.assertNotIn("proxies", output)
                for key in ("rules", "rule-providers", "dns", "mode", "log-level"):
                    self.assertEqual(output[key], original[key])

    def test_subscription_file_validation_and_no_url_in_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-url.txt"
            urls = ["https://example.org/sub?token=SECRET-ONE",
                    "https://example.org/sub2?token=SECRET-TWO"]
            path.write_text("\n".join(urls) + "\n", encoding="utf-8")
            self.assertEqual(read_subscription_urls(path), urls)
            for contents in (
                "http://example.org/sub?token=SECRET-TWO",
                "https://example.invalid/REPLACE-WITH-YOUR-SUBSCRIPTION",
                "https://example.org/sub?token=SECRET-TWO\nhttps://example.org/sub?token=SECRET-TWO",
                "https://example.org:wrong/sub?token=SECRET-TWO",
                "\n",
            ):
                with self.subTest(contents=contents[:12]):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises(ValueError) as raised:
                        read_subscription_urls(path)
                    self.assertNotIn("SECRET", str(raised.exception))

    def test_use_url_validator_rejects_malformed_and_mixed_node_sources(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "cannot be mixed"):
            build_loon_selection(source, {"private": PROVIDERS["personal"]},
                                 subscription_urls=["https://example.org/sub"])
        for bad in ("http://example.org/sub", "file:///private/node.yaml"):
            result = build_loon_selection(source,
                                          subscription_urls=["https://example.org/sub"])
            result["proxy-groups"][0]["use-url"] = [bad]
            with self.assertRaises(ValueError):
                validate_profile(result)
        bad = build_loon_selection(source,
                                   subscription_urls=["https://example.org/sub"])
        # Inject into ALL, which actually owns use-url after the refactor.
        next(g for g in bad["proxy-groups"] if g["name"] == "ALL")["include-all"] = True
        with self.assertRaisesRegex(ValueError, "cannot mix"):
            validate_profile(bad)

    def test_native_layout_experiments_single_level_provider_selection(self):
        """Native layout keeps Auto/Fallback and direct nodes on one level."""
        node = {"name": "Experiment Node", "type": "ss",
                "server": "198.51.100.7", "port": 443,
                "cipher": "aes-128-gcm", "password": "example-only"}
        source_modes = (
            ("providers", {"providers": PROVIDERS}, []),
            ("local", {"nodes": [node]}, ["Experiment Node"]),
            ("use-url", {"subscription_urls": ["https://example.org/sub"]}, []),
        )
        for profile_name in PROFILE_FILES.values():
            original = yaml.safe_load((ROOT / profile_name).read_text(encoding="utf-8"))
            for mode, inputs, names in source_modes:
                with self.subTest(profile=profile_name, mode=mode):
                    result = build_loon_selection(original, layout="native", **inputs)
                    validate_profile(result)
                    self.assertEqual(result["rules"], original["rules"])
                    self.assertEqual(result["dns"], original["dns"])
                    self.assertEqual(result["rule-providers"], original["rule-providers"])
                    groups = {g["name"]: g for g in result["proxy-groups"]}
                    self.assertEqual(len(groups), 39)
                    self.assertNotIn("ALL", groups)
                    self.assertEqual(groups["Proxy"]["proxies"],
                                     ["Auto", "Fallback"] + names + ["REJECT"])
                    self.assertEqual(groups["ChatGPT"]["proxies"],
                                     ["Proxy", "Auto", "Fallback"] + names)
                    self.assertEqual(groups["Auto"]["proxies"], names + ["REJECT"])
                    self.assertEqual(groups["Fallback"]["proxies"], names + ["REJECT"])
                    for group in groups.values():
                        self.assertNotIn("include-all", group)
                        self.assertNotIn("filter", group)
                        self.assertNotIn("ALL", group.get("proxies", []))
                        dynamic = group["name"] not in {"AdBlock", "Final"}
                        if mode == "providers" and dynamic:
                            self.assertEqual(group["use"], list(PROVIDERS))
                            self.assertNotIn("use-url", group)
                        elif mode == "use-url" and dynamic:
                            self.assertEqual(group["use-url"], inputs["subscription_urls"])
                            self.assertNotIn("use", group)
                        else:
                            self.assertNotIn("use", group)
                            self.assertNotIn("use-url", group)
                    for name in ("Apple", "Microsoft", "Bilibili",
                                 "Line", "Speedtest"):
                        self.assertEqual(groups[name]["proxies"][0], "DIRECT")
                    self.assertEqual(groups["Steam"]["proxies"][0], "Proxy")
                    self.assertIn("DIRECT", groups["Steam"]["proxies"])
                    self.assertNotIn("DIRECT", groups["Proxy"]["proxies"])
                    for name in ("ChatGPT", "Gemini", "Claude", "AI"):
                        self.assertNotIn("DIRECT", groups[name]["proxies"])

    def test_native_provider_preview_matches_generator(self):
        preview = yaml.safe_load((ROOT / "StashKit-Native-Preview.yaml")
                                 .read_text(encoding="utf-8"))
        original = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        expected = build_loon_selection(original,
                                        providers={"personal": PROVIDERS["personal"]},
                                        layout="native")
        self.assertNotIn("proxy-providers", preview)
        self.assertEqual(preview["proxy-groups"], expected["proxy-groups"])
        for key in ("dns", "rules", "rule-providers", "mode", "log-level"):
            self.assertEqual(preview[key], expected[key])
        preview["proxy-providers"] = {"personal": PROVIDERS["personal"]}
        validate_profile(preview)

    def test_native_layout_rejects_invalid_mode(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "layout"):
            build_loon_selection(source, providers=PROVIDERS, layout="unknown")

    def test_published_native_profile_is_valid_and_usable_for_generation(self):
        for filename in NATIVE_PROFILE_FILES.values():
            source = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
            validate_profile(source)
            self.assertEqual(source["proxy-providers"],
                             {"personal": {"path": "./providers/personal.yaml"}})
            generated = build_loon_selection(source, providers=PROVIDERS,
                                             layout="native")
            validate_profile(generated)
            self.assertEqual(generated["proxy-providers"], PROVIDERS)
            groups = {g["name"]: g for g in generated["proxy-groups"]}
            self.assertEqual(len(groups), 39)
            self.assertNotIn("ALL", groups)
            self.assertEqual(groups["Proxy"]["use"], list(PROVIDERS))
            self.assertEqual(groups["Proxy"]["proxies"],
                             ["Auto", "Fallback", "REJECT"])
            self.assertEqual(source["rules"], generated["rules"])
            self.assertEqual(source["dns"], generated["dns"])

    def test_private_output_folder_is_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("dist/", ignore)
        self.assertIn("*.stoverride", ignore)


if __name__ == "__main__":
    unittest.main()
