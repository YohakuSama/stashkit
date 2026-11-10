#!/usr/bin/env python3
"""Build the privacy and offline profiles from the canonical StashKit.yaml."""
import argparse
import re
from pathlib import Path

import yaml

from build_loon_selection import build_loon_selection
from release_meta import PROFILE_VERSION, RULES_PATH_PREFIX

ROOT = Path(__file__).resolve().parents[1]
HEADER = f"# StashKit {PROFILE_VERSION}\n"
PRIVACY_HEADER = f"# StashKit {PROFILE_VERSION} — privacy DNS\n"
LOCAL_HEADER = f"# StashKit {PROFILE_VERSION} — local rule providers\n"
SELF_HOSTED_HEADER = f"# StashKit {PROFILE_VERSION} — self-hosted node\n"
SUBSCRIPTION_BLOCK = (
    "# Edit the subscription URL locally; never publish private subscription credentials.\n"
    "proxy-providers:\n"
    "  Airport:\n"
    "    # Replace this URL with your private Clash/Stash YAML subscription.\n"
    "    url: 'https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION'\n"
    "    path: ./providers/stashkit-airport.yaml\n"
    "    interval: 3600\n"
)
SELF_HOSTED_BLOCK = (
    "# Replace this local node definition; keep the name SelfHosted for group references.\n"
    "proxies:\n"
    "  - name: SelfHosted\n"
    "    type: ss\n"
    "    server: replace-me.invalid\n"
    "    port: 443\n"
    "    cipher: aes-128-gcm\n"
    "    password: 'REPLACE-WITH-YOUR-PASSWORD'\n"
)

PRIVACY_DNS_RULE = '  - "DOMAIN,dns.alidns.com,Proxy"\n'
URL_LINE = re.compile(
    r"^    url: https://raw\.githubusercontent\.com/YohakuSama/stashkit/"
    r"[0-9a-f]{40}/rules/[A-Za-z0-9_.-]+\.txt\n", re.M
)
INTERVAL_LINE = re.compile(r"^    interval: 86400\n", re.M)
LOCAL_PATH = re.compile(r"^    path: " + re.escape(RULES_PATH_PREFIX) + r"[\w.-]+\.txt$", re.M)


def replace_once(content, old, new, context):
    if content.count(old) != 1:
        raise ValueError(f"{context}: expected exactly one source occurrence")
    return content.replace(old, new, 1)


def privacy_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = replace_once(content, HEADER, PRIVACY_HEADER, "profile header")
    content = replace_once(content, "  follow-rule: false\n", "  follow-rule: true\n", "privacy DNS")
    return replace_once(content, "rules:\n",
                        "rules:\n" + PRIVACY_DNS_RULE, "privacy routing")


def local_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = replace_once(content, HEADER, LOCAL_HEADER, "profile header")
    parts = content.split("\nrule-providers:\n")
    if len(parts) != 2:
        raise ValueError("Expected one rule-providers section")
    sections = parts[1].split("\nrules:\n")
    if len(sections) != 2:
        raise ValueError("Expected one rules section after rule-providers")
    providers, urls = URL_LINE.subn("", sections[0])
    providers, intervals = INTERVAL_LINE.subn("", providers)
    if (urls, intervals) != (54, 54) or len(LOCAL_PATH.findall(providers)) != 54:
        raise ValueError("Expected 54 pinned remote providers with local cache paths")
    return parts[0] + "\nrule-providers:\n" + providers + "\nrules:\n" + sections[1]



def subscription_profile(config=None):
    """Keep the old Subscription filename as an alias of the official main profile."""
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    if content.count("      - Airport\n") != 38 or content.count("proxy-providers:\n") != 1:
        raise ValueError("Expected 38 policy groups bound to the official Airport provider")
    return content


def self_hosted_profile(config=None):
    """Single-file static self-hosted node, reusing all canonical routing rules.

    Only the top-level proxies node needs editing by the end user. Its fixed
    name is deliberately referenced in every node-capable group, without
    relying on include-all, remote subscriptions, or a second local file.
    """
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    if content.count("      - Airport\n") != 38:
        raise ValueError("Expected exactly 38 node-capable groups bound to Airport")
    content = replace_once(content, HEADER, SELF_HOSTED_HEADER, "self-hosted profile header")
    content = replace_once(content, SUBSCRIPTION_BLOCK, SELF_HOSTED_BLOCK, "node source block")
    begin, marker, rest = content.partition("proxy-groups:\n")
    if not marker:
        raise ValueError("Expected one proxy-groups section")
    groups_text, marker, end = rest.partition("\nrule-providers:\n")
    if not marker:
        raise ValueError("Expected rule-providers after proxy-groups")
    matches = list(re.finditer(r'^  - name: "([^"]+)"
    outputs = {
        "StashKit-Privacy.yaml": privacy_profile(config),
        "StashKit-Subscription.yaml": subscription_profile(config),
        "StashKit-SelfHosted.yaml": self_hosted_profile(config),
        "StashKit-Local.yaml": local_profile(config),
    }
    # ALL remains an explicit compatibility variant, never a default alias.
    for filename, content in (("StashKit-ALL.yaml", config),
                              ("StashKit-Privacy-ALL.yaml", outputs["StashKit-Privacy.yaml"]),
                              ("StashKit-Local-ALL.yaml", outputs["StashKit-Local.yaml"])):
        legacy = build_loon_selection(yaml.safe_load(content),
                                      providers={"binding": {"path": "./unused.yaml"}},
                                      layout="nested")
        legacy.pop("proxy-providers")
        for group in legacy["proxy-groups"]:
            group.pop("use", None)
            if group["name"] in {"Auto", "Fallback", "ALL"}:
                group.update({"include-all": True, "filter": ".*"})
        outputs[filename] = (content.splitlines()[0] + " — legacy ALL compatibility\n"
                             + yaml.safe_dump(legacy, sort_keys=False, allow_unicode=True))
    source = yaml.safe_load(config)
    for filename, layout in (("StashKit-Loon-Preview.yaml", "nested"),
                             ("StashKit-Native-Preview.yaml", "native")):
        preview = build_loon_selection(source,
                                       providers={"personal": {"path": "./providers/personal.yaml"}},
                                       layout=layout)
        preview.pop("proxy-providers")
        outputs[filename] = (f"# StashKit {PROFILE_VERSION} — provider reference only\n"
                             "# Define a real personal provider before importing this reference.\n"
                             + yaml.safe_dump(preview, sort_keys=False, allow_unicode=True))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    outputs = derived_profiles(source)
    if args.check:
        mismatches = [name for name, value in outputs.items()
                      if (ROOT / name).read_bytes() != value.encode("utf-8")]
        if mismatches:
            raise ValueError(f"Derived profiles differ from canonical source: {mismatches}")
        print("PASS: 40-group subscription, self-hosted, and compatibility variants match canonical source")
    else:
        for name, value in outputs.items():
            (ROOT / name).write_text(value, encoding="utf-8")
        print("Updated derived profiles and explicit compatibility variants from StashKit.yaml")


if __name__ == "__main__":
    main()
, groups_text, re.M))
    if len(matches) != 40:
        raise ValueError("Expected 40 canonical policy groups")
    names = [match.group(1) for match in matches]
    if len(set(names)) != 40:
        raise ValueError("Duplicate canonical policy groups")
    output = []
    node_groups = 0
    for index, match in enumerate(matches):
        name = match.group(1)
        end_index = matches[index + 1].start() if index + 1 < len(matches) else len(groups_text)
        block = groups_text[match.start():end_index]
        if name not in {"AdBlock", "Final"}:
            block = replace_once(block, "    use:\n      - Airport\n", "", name + " subscription binding")
            node_groups += 1
            if name in {"Auto", "Fallback"}:
                block = replace_once(block, "    proxies: []\n",
                                     "    proxies:\n      - SelfHosted\n", name + " node pool")
            elif name == "Proxy":
                block = replace_once(block, "      - REJECT\n",
                                     "      - SelfHosted\n      - REJECT\n", name + " node choice")
            else:
                block = replace_once(block, "    icon: ",
                                     "      - SelfHosted\n    icon: ", name + " node choice")
        output.append(block)
    if node_groups != 38:
        raise ValueError("Expected 38 self-hosted node groups")
    result = begin + "proxy-groups:\n" + "".join(output) + "\nrule-providers:\n" + end
    if "      - Airport\n" in result or "proxy-providers:" in result:
        raise ValueError("Remote subscription binding leaked into self-hosted template")
    return result


def derived_profiles(config):
    outputs = {
        "StashKit-Privacy.yaml": privacy_profile(config),
        "StashKit-Subscription.yaml": subscription_profile(config),
        "StashKit-Local.yaml": local_profile(config),
    }
    # ALL remains an explicit compatibility variant, never a default alias.
    for filename, content in (("StashKit-ALL.yaml", config),
                              ("StashKit-Privacy-ALL.yaml", outputs["StashKit-Privacy.yaml"]),
                              ("StashKit-Local-ALL.yaml", outputs["StashKit-Local.yaml"])):
        legacy = build_loon_selection(yaml.safe_load(content),
                                      providers={"binding": {"path": "./unused.yaml"}},
                                      layout="nested")
        legacy.pop("proxy-providers")
        for group in legacy["proxy-groups"]:
            group.pop("use", None)
            if group["name"] in {"Auto", "Fallback", "ALL"}:
                group.update({"include-all": True, "filter": ".*"})
        outputs[filename] = (content.splitlines()[0] + " — legacy ALL compatibility\n"
                             + yaml.safe_dump(legacy, sort_keys=False, allow_unicode=True))
    source = yaml.safe_load(config)
    for filename, layout in (("StashKit-Loon-Preview.yaml", "nested"),
                             ("StashKit-Native-Preview.yaml", "native")):
        preview = build_loon_selection(source,
                                       providers={"personal": {"path": "./providers/personal.yaml"}},
                                       layout=layout)
        preview.pop("proxy-providers")
        outputs[filename] = (f"# StashKit {PROFILE_VERSION} — provider reference only\n"
                             "# Define a real personal provider before importing this reference.\n"
                             + yaml.safe_dump(preview, sort_keys=False, allow_unicode=True))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    outputs = derived_profiles(source)
    if args.check:
        mismatches = [name for name, value in outputs.items()
                      if (ROOT / name).read_bytes() != value.encode("utf-8")]
        if mismatches:
            raise ValueError(f"Derived profiles differ from canonical source: {mismatches}")
        print("PASS: 40-group editable subscription defaults and compatibility variants match canonical source")
    else:
        for name, value in outputs.items():
            (ROOT / name).write_text(value, encoding="utf-8")
        print("Updated derived profiles and explicit compatibility variants from StashKit.yaml")


if __name__ == "__main__":
    main()
