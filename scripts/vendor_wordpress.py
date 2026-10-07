#!/usr/bin/env python3
from __future__ import annotations
import mimetypes, os, re, sys, urllib.parse, urllib.request
from pathlib import Path

SITE = "https://valorizeie.com"
ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets" / "vendor"
PAGES = {
    "index.html": SITE + "/",
    "our-services/index.html": SITE + "/our-services/",
    "sobre-nosotros/index.html": SITE + "/sobre-nosotros/",
    "nuestro-equipo/index.html": SITE + "/nuestro-equipo/",
    "contacts/index.html": SITE + "/contacts/",
}
ALLOWED_PREFIXES = ("/wp-content/", "/wp-includes/")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ValorizeStaticMirror/1.0)"}
URL_ATTR_RE = re.compile(r'(?P<attr>href|src)=([\\'"])(?P<url>.*?)(?P=2)', re.I | re.S)
SRCSET_RE = re.compile(r'(?P<attr>srcset)=([\\'"])(?P<value>.*?)(?P=2)', re.I | re.S)
CSS_URL_RE = re.compile(r'url\\((?P<q>[\\'"]?)(?P<url>.*?)(?P=q)\\)', re.I)
ABS_SITE_RE = re.compile(r'https?://valorizeie\\.com(?P<path>/[^\\s\\'")<>]+)', re.I)

downloaded = {}
queue = []
failures = []

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def clean_url(url, base):
    url = url.strip()
    if not url or url.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
        return url
    if url.startswith("//"):
        url = "https:" + url
    return urllib.parse.urljoin(base, url)

def same_site_asset(url):
    p = urllib.parse.urlsplit(url)
    return p.netloc.lower() == "valorizeie.com" and p.path.startswith(ALLOWED_PREFIXES)

def local_path_for(url):
    p = urllib.parse.urlsplit(url)
    path = p.path.lstrip("/")
    if not path or path.endswith("/"):
        path += "index"
    return VENDOR / path

def local_ref(from_file, target):
    return Path(os.path.relpath(target, from_file.parent)).as_posix()

def enqueue(url):
    if url not in downloaded and url not in queue:
        queue.append(url)

def rewrite_asset_url(raw, base_url, out_file):
    abs_url = clean_url(raw, base_url)
    if same_site_asset(abs_url):
        enqueue(abs_url)
        return local_ref(out_file, local_path_for(abs_url))
    return raw

def rewrite_css_text(text, source_url, out_file):
    def repl_url(m):
        raw = m.group("url")
        new = rewrite_asset_url(raw, source_url, out_file)
        q = m.group("q") or ""
        return "url(" + q + new + q + ")"
    text = CSS_URL_RE.sub(repl_url, text)
    def repl_abs(m):
        return rewrite_asset_url(SITE + m.group("path"), source_url, out_file)
    return ABS_SITE_RE.sub(repl_abs, text)

def rewrite_html(html, page_url, out_file):
    def attr_repl(m):
        attr, quote, raw = m.group("attr"), m.group(2), m.group("url")
        abs_url = clean_url(raw, page_url)
        if abs_url.startswith(SITE):
            p = urllib.parse.urlsplit(abs_url)
            if p.path in ("/", ""):
                return attr + "=" + quote + local_ref(out_file, ROOT / "index.html") + quote
            for rel, src in PAGES.items():
                if urllib.parse.urlsplit(src).path.rstrip("/") == p.path.rstrip("/"):
                    return attr + "=" + quote + local_ref(out_file, ROOT / rel) + quote
        if same_site_asset(abs_url):
            enqueue(abs_url)
            return attr + "=" + quote + local_ref(out_file, local_path_for(abs_url)) + quote
        return m.group(0)
    html = URL_ATTR_RE.sub(attr_repl, html)
    def srcset_repl(m):
        quote = m.group(2)
        items = []
        for item in m.group("value").split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split()
            new = rewrite_asset_url(parts[0], page_url, out_file)
            suffix = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""
            items.append(new + suffix)
        return m.group("attr") + "=" + quote + ", ".join(items) + quote
    html = SRCSET_RE.sub(srcset_repl, html)
    return rewrite_css_text(html, page_url, out_file)

def save_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def process_asset(url):
    if url in downloaded:
        return
    out = local_path_for(url)
    try:
        data = fetch(url)
        content_type, _ = mimetypes.guess_type(urllib.parse.urlsplit(url).path)
        if content_type == "text/css" or out.suffix.lower() == ".css":
            text = data.decode("utf-8", errors="replace")
            data = rewrite_css_text(text, url, out).encode("utf-8")
        save_bytes(out, data)
        downloaded[url] = out
        print("asset", url, "->", out.relative_to(ROOT))
    except Exception as e:
        failures.append((url, repr(e)))
        print("WARN asset failed:", url, e, file=sys.stderr)

def main():
    VENDOR.mkdir(parents=True, exist_ok=True)
    for rel, page_url in PAGES.items():
        out = ROOT / rel
        print("page", page_url, "->", rel)
        raw = fetch(page_url).decode("utf-8", errors="replace")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rewrite_html(raw, page_url, out), encoding="utf-8")
    while queue:
        process_asset(queue.pop(0))
    lines = [
        "# Valorize static migration report",
        "",
        "- Source: " + SITE,
        "- Mirrored pages: " + str(len(PAGES)),
        "- Vendored assets: " + str(len(downloaded)),
        "- Failed assets: " + str(len(failures)),
        "",
        "## Known dynamic exceptions",
        "",
        "- WordPress/Elementor admin editing is not part of the static build.",
        "- Forminator/WordPress AJAX forms may need a new form backend before WordPress can be retired.",
        "- Third-party embeds such as YouTube or maps remain external by design.",
    ]
    if failures:
        lines += ["", "## Failed downloads", ""]
        lines += ["- " + u + " — " + err for u, err in failures]
    (ROOT / "MIGRATION_REPORT.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print("Completed with", len(failures), "failed assets." if failures else "failed assets.")

if __name__ == "__main__":
    main()

# workflow trigger
