"""Resolve private node sources locally for explicit, single-level selectors.

No remote converter receives the subscription. Errors deliberately omit source
URLs, headers, node names and YAML excerpts because they may contain secrets.
"""
import copy
import base64
import re
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

import yaml

MAX_SOURCE_BYTES = 16 * 1024 * 1024
BENCHMARK_KEYS = ("benchmark-url", "benchmark-timeout")
DEFAULT_BENCHMARK = {"benchmark-url": "http://www.bing.com", "benchmark-timeout": 5}


def subscription_url(url):
    try:
        parts = urlsplit(url)
        valid = (parts.scheme == "https" and bool(parts.hostname)
                 and parts.port != 0 and not parts.fragment)
    except (ValueError, TypeError):
        valid = False
    if not valid or "example.invalid" in url or "REPLACE-" in url:
        raise ValueError("Subscription URLs must be real HTTPS links without fragments")
    return url


class PrivateLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate keys without echoing their contents."""


def unique_mapping(loader, node):
    result = {}
    for key, value in node.value:
        name = loader.construct_object(key, deep=True)
        try:
            duplicate = name in result
        except TypeError:
            raise ValueError("Node source has an invalid YAML key") from None
        if duplicate:
            raise ValueError("Node source has duplicate YAML keys")
        result[name] = loader.construct_object(value, deep=True)
    return result


PrivateLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_private_yaml(content):
    try:
        return yaml.load(content, Loader=PrivateLoader)
    except (yaml.YAMLError, UnicodeError):
        raise ValueError("Node source is not valid UTF-8 Clash/Stash YAML") from None


class HTTPSRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        subscription_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        # Do not forward a private authorization header to another host.
        if urlsplit(req.full_url).netloc != urlsplit(newurl).netloc:
            for name in list(redirected.headers):
                if name.lower() not in {"accept", "user-agent"}:
                    redirected.remove_header(name)
        return redirected


def fetch_subscription(url, headers=None):
    subscription_url(url)
    try:
        request_headers = {
            "User-Agent": "Stash", "Accept": "application/yaml, text/plain",
            **(headers or {}),
        }
        parts = urlsplit(url)
        if parts.username is not None:
            credentials = unquote(parts.username) + ":" + unquote(parts.password or "")
            request_headers = {k: v for k, v in request_headers.items() if k.lower() != "authorization"}
            request_headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()
            url = urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[1], parts.path,
                             parts.query, ""))
        request = urllib.request.Request(url, headers=request_headers)
        opener = urllib.request.build_opener(HTTPSRedirects())
        with opener.open(request, timeout=20) as response:
            if response.status != 200:
                raise ValueError("Unexpected subscription status")
            content = response.read(MAX_SOURCE_BYTES + 1)
        if len(content) > MAX_SOURCE_BYTES:
            raise ValueError("Subscription is too large")
        return content.decode("utf-8-sig")
    except Exception:
        raise ValueError("Cannot download a valid HTTPS node subscription") from None


def resolve_node_sources(nodes=None, providers=None, subscription_urls=None,
                         base_dir=Path("."), fetcher=fetch_subscription):
    """Expand all sources in declaration order; never return a partial pool."""
    result = []
    by_name = {}

    def add(entries, defaults=None, pattern=None):
        if not isinstance(entries, list) or not entries:
            raise ValueError("Node source must contain a nonempty proxies list")
        selected = 0
        for original in entries:
            if (not isinstance(original, dict)
                    or not isinstance(original.get("name"), str)
                    or not original["name"].strip()
                    or not isinstance(original.get("type"), str)
                    or original["type"].lower() in {
                        "direct", "reject", "reject-drop", "select", "url-test",
                        "fallback", "load-balance", "relay", "pass",
                    }
                    or not original["type"].strip()
                    or not isinstance(original.get("server"), str)
                    or not original["server"].strip()
                    or type(original.get("port")) is not int
                    or not 1 <= original["port"] <= 65535):
                raise ValueError("Node source contains an invalid proxy entry")
            if pattern is not None and not pattern.search(original["name"]):
                continue
            selected += 1
            node = copy.deepcopy(original)
            for key, value in (defaults or {}).items():
                node.setdefault(key, value)
            for key, value in DEFAULT_BENCHMARK.items():
                node.setdefault(key, value)
            previous = by_name.get(node["name"])
            if previous is not None:
                if previous != node:
                    raise ValueError("Conflicting node names across sources; rename them locally")
                continue
            by_name[node["name"]] = node
            result.append(node)
        if not selected:
            raise ValueError("Provider filter selected no nodes")

    if nodes:
        add(nodes)
    for spec in (providers or {}).values():
        if not isinstance(spec, dict):
            raise ValueError("Invalid proxy-provider definition")
        try:
            pattern = re.compile(spec["filter"]) if "filter" in spec else None
            headers = spec.get("headers", {})
            if not isinstance(headers, dict) or any(not isinstance(k, str) for k in headers):
                raise ValueError("Unsupported provider headers")
            normalized = {}
            for key, value in headers.items():
                if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
                    value = ", ".join(value)
                if not isinstance(value, str):
                    raise ValueError("Unsupported provider headers")
                normalized[key] = value
            if spec.get("url"):
                content = fetcher(subscription_url(spec["url"]), normalized)
            else:
                path = Path(spec["path"])
                path = path if path.is_absolute() else Path(base_dir) / path
                content = path.read_text(encoding="utf-8-sig")
            data = load_private_yaml(content)
        except Exception:
            raise ValueError("Cannot load a provider; check its URL, headers, path and filter locally") from None
        defaults = {key: spec[key] for key in BENCHMARK_KEYS if key in spec}
        add(data.get("proxies") if isinstance(data, dict) else None, defaults, pattern)
    for url in subscription_urls or []:
        try:
            data = load_private_yaml(fetcher(subscription_url(url), {}))
        except Exception:
            raise ValueError("Cannot load a subscription as Clash/Stash YAML") from None
        add(data.get("proxies") if isinstance(data, dict) else None)
    if not result:
        raise ValueError("No usable nodes; refusing to generate an empty strategy pool")
    return result
