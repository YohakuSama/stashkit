"""Validate the documented Stash subset used by the shipped StashKit files.

This is intentionally a project schema, not a schema for every Stash feature.
Extend it alongside tests when adopting another documented native feature.
"""
import ipaddress
import re
from urllib.parse import urlsplit

from rule_sources import valid_domain

BUILTINS = {"DIRECT", "REJECT", "REJECT-DROP"}
PROTOCOLS = {"TCP", "UDP", "HTTP", "TLS", "QUIC", "STUN"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, allowed, required, where):
    require(isinstance(value, dict), f"{where}: expected a mapping")
    require(all(isinstance(key, str) for key in value), f"{where}: keys must be strings")
    require(not (set(value) - allowed), f"{where}: unknown StashKit keys {set(value) - allowed}")
    require(required <= set(value), f"{where}: missing keys {required - set(value)}")


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), f"{where}: expected nonempty string")


def string_list(value, where, nonempty=False):
    require(isinstance(value, list), f"{where}: expected list")
    require(not nonempty or bool(value), f"{where}: list must not be empty")
    for entry in value:
        text(entry, where)
    require(len(value) == len(set(value)), f"{where}: duplicate list entries")


def http_url(value, where):
    text(value, where)
    parts = urlsplit(value)
    require(parts.scheme in {"https", "http"} and bool(parts.hostname), f"{where}: expected HTTP(S) URL")
    # Accessing .port also rejects malformed/non-numeric ports.
    _ = parts.port


def dns_server(value, where, bootstrap=False):
    text(value, where)
    if value == "system":
        return
    if "://" not in value:
        ipaddress.ip_address(value)
        return
    parts = urlsplit(value)
    require(parts.scheme in {"https", "tls", "quic", "tcp", "udp"} and bool(parts.hostname),
            f"{where}: unsupported DNS address {value}")
    _ = parts.port
    if bootstrap:
        ipaddress.ip_address(parts.hostname)


def validate_dns(dns):
    fields(dns, {"default-nameserver", "nameserver", "proxy-server-nameserver", "nameserver-policy",
                 "follow-rule", "fake-ip-range", "fake-ip-filter", "ipv6"},
           {"nameserver"}, "dns")
    for key in ("default-nameserver", "nameserver", "proxy-server-nameserver"):
        if key in dns:
            string_list(dns[key], f"dns.{key}", nonempty=True)
            for value in dns[key]:
                dns_server(value, f"dns.{key}", bootstrap=key == "default-nameserver")
    for key in ("follow-rule", "ipv6"):
        if key in dns:
            require(type(dns[key]) is bool, f"dns.{key}: expected boolean")
    if "fake-ip-range" in dns:
        text(dns["fake-ip-range"], "dns.fake-ip-range")
        require(ipaddress.ip_network(dns["fake-ip-range"], strict=False).version == 4,
                "dns.fake-ip-range: expected IPv4 prefix")
    if "fake-ip-filter" in dns:
        string_list(dns["fake-ip-filter"], "dns.fake-ip-filter")
    policies = dns.get("nameserver-policy", {})
    require(isinstance(policies, dict), "dns.nameserver-policy: expected mapping")
    for name, servers in policies.items():
        text(name, "dns.nameserver-policy key")
        servers = servers if isinstance(servers, list) else [servers]
        string_list(servers, f"dns.nameserver-policy.{name}", nonempty=True)
        for value in servers:
            dns_server(value, f"dns.nameserver-policy.{name}")


def validate_headers(headers, where):
    require(isinstance(headers, dict), f"{where}: expected mapping")
    for name, value in headers.items():
        text(name, where)
        if isinstance(value, list):
            string_list(value, where, nonempty=True)
        else:
            text(value, where)


def validate_matcher(kind, value, where):
    text(value, where)
    if kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
        valid_domain(value)
    elif kind == "DOMAIN-REGEX":
        try:
            re.compile(value)
        except re.error as error:
            raise ValueError(f"{where}: invalid regular expression") from error
    elif kind in {"IP-CIDR", "IP-CIDR6"}:
        version = ipaddress.ip_network(value, strict=False).version
        require(version == (4 if kind == "IP-CIDR" else 6), f"Wrong address family: {where}")
    elif kind == "IP-ASN":
        require(value.isdigit() and 0 < int(value) <= 4294967295, f"Invalid ASN: {where}")
    elif kind == "GEOIP":
        require(value in {"LAN", "UNKNOWN"} or bool(re.fullmatch(r"[A-Z]{2}", value)),
                f"Invalid GEOIP value: {where}")
    elif kind == "GEOSITE":
        require(bool(re.fullmatch(r"[A-Za-z0-9_@!.-]+", value)), f"Invalid GEOSITE value: {where}")
    elif kind == "PROTOCOL":
        require(value in PROTOCOLS, f"Unsupported protocol: {where}")
    else:
        raise ValueError(f"Unsupported matcher: {where}")


def validate_inline(spec, where):
    fields(spec, {"type", "behavior", "payload"}, {"type", "behavior", "payload"}, where)
    string_list(spec["payload"], where + ".payload", nonempty=True)
    for row in spec["payload"]:
        if spec["behavior"] == "domain":
            valid_domain(row[2:] if row.startswith("+.") else row)
        elif spec["behavior"] == "ipcidr":
            ipaddress.ip_network(row, strict=False)
        else:
            pieces = row.split(",")
            require(len(pieces) >= 2, f"Malformed inline rule: {row}")
            kind, value, *options = pieces
            validate_matcher(kind, value, row)
            require(not options or (options == ["no-resolve"] and
                    kind in {"GEOIP", "IP-ASN", "IP-CIDR", "IP-CIDR6"}),
                    f"Unsupported inline options: {row}")


def validate_proxy_providers(providers):
    require(isinstance(providers, dict), "proxy-providers: expected mapping")
    for name, spec in providers.items():
        text(name, "proxy-providers name")
        where = f"proxy-providers.{name}"
        fields(spec, {"url", "path", "interval", "filter", "headers", "benchmark-url", "benchmark-timeout"},
               {"url"}, where)
        http_url(spec["url"], where + ".url")
        if "benchmark-url" in spec:
            http_url(spec["benchmark-url"], where + ".benchmark-url")
        for key in ("interval", "benchmark-timeout"):
            if key in spec:
                require(type(spec[key]) is int and spec[key] > 0, f"{where}.{key}: expected positive integer")
        for key in ("path", "filter"):
            if key in spec:
                text(spec[key], where + "." + key)
        if "headers" in spec:
            validate_headers(spec["headers"], where + ".headers")


def validate_profile(profile):
    fields(profile, {"mode", "log-level", "dns", "proxy-groups", "rule-providers", "rules", "proxy-providers"},
           {"mode", "dns", "proxy-groups", "rule-providers", "rules"}, "profile")
    require(profile["mode"] in {"rule", "global", "direct"}, "mode: unsupported value")
    require(profile.get("log-level", "silent") in {"silent", "info", "warning", "error", "debug"},
            "log-level: unsupported value")
    validate_dns(profile["dns"])
    proxy_providers = profile.get("proxy-providers", {})
    validate_proxy_providers(proxy_providers)
    groups = profile["proxy-groups"]
    require(isinstance(groups, list) and bool(groups), "proxy-groups: expected nonempty list")
    names = []
    for group in groups:
        fields(group, {"name", "type", "proxies", "use", "include-all", "filter", "icon", "interval",
                       "tolerance", "lazy", "hidden"}, {"name", "type"}, "proxy-group")
        text(group["name"], "proxy-group.name")
        require(group["type"] in {"select", "url-test", "fallback", "load-balance", "relay"},
                f"{group['name']}: unsupported group type {group['type']}")
        names.append(group["name"])
        for key in ("proxies", "use"):
            if key in group:
                string_list(group[key], f"{group['name']}.{key}")
        for key in ("include-all", "lazy", "hidden"):
            if key in group:
                require(type(group[key]) is bool, f"{group['name']}.{key}: expected boolean")
        for key in ("interval", "tolerance"):
            if key in group:
                require(type(group[key]) is int, f"{group['name']}.{key}: expected integer")
        if "interval" in group:
            require(group["interval"] > 0, f"{group['name']}: interval must be positive")
        if "tolerance" in group:
            require(group["type"] == "url-test" and group["tolerance"] >= 0,
                    f"{group['name']}: tolerance is for url-test and must be nonnegative")
        if "icon" in group:
            http_url(group["icon"], f"{group['name']}.icon")
        if "filter" in group:
            text(group["filter"], f"{group['name']}.filter")
    require(len(names) == len(set(names)), "proxy-groups: duplicate names")
    require(not (set(names) & BUILTINS), "proxy-groups: names conflict with built-in policies")
    graph = {}
    for group in groups:
        children = group.get("proxies", [])
        require(set(children) <= set(names) | BUILTINS, f"{group['name']}: unknown policy reference")
        require(set(group.get("use", [])) <= set(proxy_providers), f"{group['name']}: unknown provider reference")
        graph[group["name"]] = [name for name in children if name in names]
    visiting, visited = set(), set()

    def visit(name):
        require(name not in visiting, f"proxy-groups: cyclic reference involving {name}")
        if name in visited:
            return
        visiting.add(name)
        for child in graph[name]:
            visit(child)
        visiting.remove(name)
        visited.add(name)

    for name in names:
        visit(name)
    providers = profile["rule-providers"]
    require(isinstance(providers, dict), "rule-providers: expected mapping")
    for name, spec in providers.items():
        text(name, "rule-providers name")
        fields(spec, {"type", "payload", "behavior", "format", "url", "path", "interval", "headers"},
               {"behavior"}, f"rule-providers.{name}")
        require(spec["behavior"] in {"domain", "ipcidr", "classical"}, f"{name}: invalid behavior")
        if spec.get("type") == "inline":
            validate_inline(spec, f"rule-providers.{name}")
            continue
        require("type" not in spec and "payload" not in spec, f"{name}: unsupported provider type")
        require("format" in spec, f"{name}: format required")
        require("url" in spec or "path" in spec, f"{name}: remote URL or local path required")
        if "url" in spec:
            require("interval" in spec, f"{name}: remote provider interval required")
        else:
            require("interval" not in spec, f"{name}: local-only provider cannot auto-update")
        require(spec["format"] in {"text", "yaml"}, f"{name}: invalid format")
        if "url" in spec:
            http_url(spec["url"], f"{name}.url")
        if "interval" in spec:
            require(type(spec["interval"]) is int and spec["interval"] > 0, f"{name}: invalid interval")
        if "headers" in spec:
            validate_headers(spec["headers"], f"{name}.headers")
        if "path" in spec:
            text(spec["path"], f"{name}.path")
    dns_refs = list(profile["dns"].get("nameserver-policy", {})) + profile["dns"].get("fake-ip-filter", [])
    for value in dns_refs:
        if value.startswith("rule-set:"):
            name = value[len("rule-set:"):]
            require(name in providers, f"Unknown DNS rule provider: {name}")
            spec = providers[name]
            require(spec["behavior"] != "ipcidr", f"DNS rule provider must match domains: {name}")
            if spec.get("type") == "inline" and spec["behavior"] == "classical":
                require(all(row.startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-REGEX,"))
                            for row in spec["payload"]), f"DNS inline provider must contain only domains: {name}")
    string_list(profile["rules"], "rules", nonempty=True)
    require(sum(rule.startswith("MATCH,") for rule in profile["rules"]) == 1 and
            profile["rules"][-1].startswith("MATCH,"), "MATCH must occur exactly once at the end")
    for rule in profile["rules"]:
        kind, *args = rule.split(",")
        require(kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-REGEX", "PROTOCOL", "GEOIP", "GEOSITE", "IP-CIDR", "IP-CIDR6",
                         "IP-ASN", "RULE-SET", "MATCH"}, f"Unsupported StashKit rule: {rule}")
        required = 1 if kind == "MATCH" else 2
        require(len(args) >= required, f"Malformed rule: {rule}")
        policy = args[required - 1]
        options = args[required:]
        require(policy in set(names) | BUILTINS, f"Unknown rule policy: {rule}")
        require(set(options) <= {"no-resolve", "no-track"} and len(options) == len(set(options)),
                f"Unsupported or duplicated rule option: {rule}")
        if "no-resolve" in options:
            require(kind in {"GEOIP", "IP-ASN", "IP-CIDR", "IP-CIDR6", "RULE-SET"},
                    f"no-resolve is not applicable: {rule}")
        if kind != "MATCH":
            text(args[0], f"Rule value: {rule}")
        if kind == "RULE-SET":
            require(args[0] in providers, f"Unknown rule provider: {rule}")
        elif kind != "MATCH":
            validate_matcher(kind, args[0], rule)


def validate_override(override):
    fields(override, {"name", "desc", "proxy-providers"}, {"name", "desc", "proxy-providers"}, "provider override")
    text(override["name"], "override.name")
    text(override["desc"], "override.desc")
    validate_proxy_providers(override["proxy-providers"])
