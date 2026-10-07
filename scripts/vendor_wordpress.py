#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SITE = "https://valorizeie.com"
HOST = "valorizeie.com"
ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets" / "vendor"

PAGES = {
    "index.html": f"{SITE}/",
    "our-services/index.html": f"{SITE}/our-services/",
    "sobre-nosotros/index.html": f"{SITE}/sobre-nosotros/",
    "nuestro-equipo/index.html": f"{SITE}/nuestro-equipo/",
    "contacts/index.html": f"{SITE}/contacts/",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ValorizeStaticMirror/2.0)"}
ASSET_PREFIXES = ("/wp-content/", "/wp-includes/")

ABS_ASSET_RE = re.compile(
    r"https?://(?:www\.)?valorizeie\.com(?P<path>/(?:wp-content|wp-includes)/[^\"'<>\s)\\]+)",
    re.I,
)
PROTO_ASSET_RE = re.compile(
    r"//(?:www\.)?valorizeie\.com(?P<path>/(?:wp-content|wp-includes)/[^\"'<>\s)\\]+)",
    re.I,
)
CSS_URL_RE = re.compile(
    r"url\(\s*(?P<quote>[\"']?)(?P<url>[^)\"']+)(?P=quote)\s*\)",
    re.I,
)
SRCSET_RE = re.compile(r"""srcset=(?P<quote>["'])(?P<value>.*?)(?P=quote)""", re.I | re.S)
ATTR_RE = re.compile(
    r"""(?P<attr>href|src|poster|data-src|data-lazy-src)=(?P<quote>["'])(?P<url>.*?)(?P=quote)""",
    re.I | re.S,
)

queue: list[str] = []
downloaded: dict[str, Path] = {}
failed: list[tuple[str, str]] = []


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def normalize_url(raw: str, base: str) -> str:
    raw = raw.replace("&#038;", "&").replace("&amp;", "&").strip()
    if raw.startswith("//"):
        raw = "https:" + raw
    return urllib.parse.urljoin(base, raw)


def is_local_asset(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return parsed.netloc.lower() in {HOST, "www." + HOST} and parsed.path.startswith(ASSET_PREFIXES)


def canonical_asset_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(("https", HOST, parsed.path, parsed.query, ""))


def local_asset_path(url: str) -> Path:
    parsed = urllib.parse.urlsplit(url)
    return VENDOR / parsed.path.lstrip("/")


def rel_ref(from_file: Path, target: Path) -> str:
    return Path(os.path.relpath(target, from_file.parent)).as_posix()


def enqueue(url: str) -> None:
    if not is_local_asset(url):
        return
    url = canonical_asset_url(url)
    if url not in downloaded and url not in queue:
        queue.append(url)


def rewrite_asset_reference(raw: str, base_url: str, current_file: Path) -> str:
    absolute = normalize_url(raw, base_url)
    if not is_local_asset(absolute):
        return raw
    absolute = canonical_asset_url(absolute)
    enqueue(absolute)
    return rel_ref(current_file, local_asset_path(absolute))


def rewrite_css(text: str, source_url: str, current_file: Path) -> str:
    def css_url_repl(match: re.Match) -> str:
        raw = match.group("url").strip()
        if raw.startswith("data:"):
            return match.group(0)
        new = rewrite_asset_reference(raw, source_url, current_file)
        quote = match.group("quote") or ""
        return f"url({quote}{new}{quote})"

    text = CSS_URL_RE.sub(css_url_repl, text)

    def abs_repl(match: re.Match) -> str:
        raw = f"{SITE}{match.group('path')}"
        return rewrite_asset_reference(raw, source_url, current_file)

    text = ABS_ASSET_RE.sub(abs_repl, text)
    text = PROTO_ASSET_RE.sub(abs_repl, text)
    return text


def rewrite_internal_links(html: str, current_file: Path, page_url: str) -> str:
    route_by_path = {
        urllib.parse.urlsplit(url).path.rstrip("/") or "/": ROOT / local
        for local, url in PAGES.items()
    }

    def attr_repl(match: re.Match) -> str:
        attr = match.group("attr")
        quote = match.group("quote")
        raw = match.group("url")
        absolute = normalize_url(raw, page_url)
        parsed = urllib.parse.urlsplit(absolute)

        if parsed.netloc.lower() in {HOST, "www." + HOST}:
            route_key = parsed.path.rstrip("/") or "/"
            if route_key in route_by_path:
                target = route_by_path[route_key]
                suffix = ""
                if parsed.query:
                    suffix += "?" + parsed.query
                if parsed.fragment:
                    suffix += "#" + parsed.fragment
                return f"{attr}={quote}{rel_ref(current_file, target)}{suffix}{quote}"

        if is_local_asset(absolute):
            localized = rewrite_asset_reference(raw, page_url, current_file)
            return f"{attr}={quote}{localized}{quote}"

        return match.group(0)

    return ATTR_RE.sub(attr_repl, html)


def rewrite_srcset(html: str, page_url: str, current_file: Path) -> str:
    def repl(match: re.Match) -> str:
        items = []
        for item in match.group("value").split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split()
            local = rewrite_asset_reference(parts[0], page_url, current_file)
            descriptor = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""
            items.append(local + descriptor)
        q = match.group("quote")
        return f"srcset={q}{', '.join(items)}{q}"

    return SRCSET_RE.sub(repl, html)


def rewrite_all_literal_assets(html: str, page_url: str, current_file: Path) -> str:
    def abs_repl(match: re.Match) -> str:
        raw = f"{SITE}{match.group('path')}"
        return rewrite_asset_reference(raw, page_url, current_file)

    html = ABS_ASSET_RE.sub(abs_repl, html)
    html = PROTO_ASSET_RE.sub(abs_repl, html)

    escaped_prefixes = [
        r"https:\/\/valorizeie.com\/wp-content\/",
        r"https:\/\/valorizeie.com\/wp-includes\/",
    ]
    local_prefixes = [
        rel_ref(current_file, VENDOR / "wp-content") + "/",
        rel_ref(current_file, VENDOR / "wp-includes") + "/",
    ]
    for old, new in zip(escaped_prefixes, local_prefixes):
        html = html.replace(old, new.replace("/", r"\/"))

    return html


def process_page(local: str, page_url: str) -> None:
    target = ROOT / local
    raw = fetch(page_url).decode("utf-8", "replace")
    target.parent.mkdir(parents=True, exist_ok=True)
    html = rewrite_internal_links(raw, target, page_url)
    html = rewrite_srcset(html, page_url, target)
    html = rewrite_all_literal_assets(html, page_url, target)
    html = rewrite_css(html, page_url, target)
    target.write_text(html, encoding="utf-8")
    print(f"page {page_url} -> {local}")


def process_asset(url: str) -> None:
    url = canonical_asset_url(url)
    if url in downloaded:
        return
    target = local_asset_path(url)
    try:
        data = fetch(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix.lower() == ".css":
            text = data.decode("utf-8", "replace")
            data = rewrite_css(text, url, target).encode("utf-8")
        target.write_bytes(data)
        downloaded[url] = target
        print(f"asset {url} -> {target.relative_to(ROOT)}")
    except Exception as exc:
        failed.append((url, repr(exc)))
        print(f"WARN asset failed: {url}: {exc}", file=sys.stderr)


def write_report() -> None:
    lines = [
        "# Valorize static migration report",
        "",
        f"- Source: {SITE}",
        f"- Mirrored pages: {len(PAGES)}",
        f"- Vendored assets: {len(downloaded)}",
        f"- Failed assets: {len(failed)}",
        "",
        "## What is now local",
        "",
        "- HTML for the five principal pages",
        "- Same-origin CSS and JavaScript referenced by those pages",
        "- Images, fonts and other same-origin resources discovered directly or through CSS",
        "",
        "## Dynamic exceptions",
        "",
        "- Forminator submissions still point to WordPress unless a new form backend is configured.",
        "- WordPress AJAX-only behaviors need a static/API replacement before WordPress can be fully retired.",
        "- External embeds such as YouTube or maps remain external by design.",
    ]
    if failed:
        lines += ["", "## Failed downloads", ""]
        lines += [f"- {url} — {err}" for url, err in failed]
    (ROOT / "MIGRATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    VENDOR.mkdir(parents=True, exist_ok=True)
    for local, page_url in PAGES.items():
        process_page(local, page_url)
    while queue:
        process_asset(queue.pop(0))
    write_report()
    if failed:
        print(f"Completed with {len(failed)} failed assets.", file=sys.stderr)
    else:
        print("Completed without asset download failures.")


if __name__ == "__main__":
    main()
