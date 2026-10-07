#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

SITE = "https://valorizeie.com"
HOST = "valorizeie.com"
ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets" / "vendor"
HEADERS = {"User-Agent": "Mozilla/5.0 (Valorize static migration)"}

SERVICES = {
    "captura-del-valor-del-suelo-catastro-e-infraestructura":
        SITE + "/services/captura-del-valor-del-suelo-catastro-e-infraestructura/",
    "analisis-economico-territorial-y-eficiencia-fiscal":
        SITE + "/services/analisis-economico-territorial-y-eficiencia-fiscal/",
    "planeacion-estrategica-del-desarrollo-urbano-y-regional":
        SITE + "/services/planeacion-estrategica-del-desarrollo-urbano-y-regional/",
    "finanzas-publicas-territoriales-y-modelos-de-gestion-financiera":
        SITE + "/services/finanzas-publicas-territoriales-y-modelos-de-gestion-financiera/",
}

SERVICE_POSTS = {
    "captura-del-valor-del-suelo-catastro-e-infraestructura": "40278",
    "analisis-economico-territorial-y-eficiencia-fiscal": "40114",
    "planeacion-estrategica-del-desarrollo-urbano-y-regional": "40277",
    "finanzas-publicas-territoriales-y-modelos-de-gestion-financiera": "41418",
}

ASSET_RE = re.compile(
    r'https?://(?:www\.)?valorizeie\.com/(?P<path>(?:wp-content|wp-includes)/[^"\'<>\s)\\]+)',
    re.I,
)
CSS_URL_RE = re.compile(r'url\(\s*(?P<q>["\']?)(?P<u>[^)"\']+)(?P=q)\s*\)', re.I)

downloaded = set()
queued = []

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def canon_asset(url: str) -> str | None:
    if url.startswith("//"):
        url = "https:" + url
    p = urllib.parse.urlsplit(url)
    if p.netloc.lower() not in {HOST, "www." + HOST}:
        return None
    if not p.path.startswith(("/wp-content/", "/wp-includes/")):
        return None
    return urllib.parse.urlunsplit(("https", HOST, p.path, p.query, ""))

def local_asset_path(url: str) -> Path:
    p = urllib.parse.urlsplit(url)
    return VENDOR / p.path.lstrip("/")

def rel(from_file: Path, to_file: Path) -> str:
    return Path(os.path.relpath(to_file, from_file.parent)).as_posix()

def enqueue(url: str):
    u = canon_asset(url)
    if u and u not in downloaded and u not in queued:
        queued.append(u)

def localize_asset(raw: str, base_url: str, current_file: Path) -> str:
    abs_url = urllib.parse.urljoin(base_url, raw.replace("&amp;", "&").replace("&#038;", "&"))
    u = canon_asset(abs_url)
    if not u:
        return raw
    enqueue(u)
    return rel(current_file, local_asset_path(u))

def rewrite_css(text: str, source_url: str, current_file: Path) -> str:
    def repl(m):
        raw = m.group("u").strip()
        if raw.startswith("data:"):
            return m.group(0)
        new = localize_asset(raw, source_url, current_file)
        q = m.group("q") or ""
        return f"url({q}{new}{q})"
    text = CSS_URL_RE.sub(repl, text)

    def abs_repl(m):
        u = "https://" + HOST + "/" + m.group("path")
        return localize_asset(u, source_url, current_file)
    return ASSET_RE.sub(abs_repl, text)

def vendor_one(url: str):
    if url in downloaded:
        return
    target = local_asset_path(url)
    try:
        data = fetch(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix.lower() == ".css":
            txt = data.decode("utf-8", "replace")
            data = rewrite_css(txt, url, target).encode("utf-8")
        target.write_bytes(data)
        downloaded.add(url)
        print("asset", url, "->", target.relative_to(ROOT))
    except Exception as exc:
        print("WARN", url, exc)

def strip_wp_runtime(html: str) -> str:
    html = re.sub(r'<link\b[^>]*(?:feed/|comments/feed/|wp-json|xmlrpc\.php|api\.w\.org)[^>]*>\s*', '', html, flags=re.I)
    html = re.sub(r'<meta\b[^>]*name=["\']generator["\'][^>]*(?:WordPress|WooCommerce)[^>]*>\s*', '', html, flags=re.I)
    html = re.sub(r'<link\b[^>]*rel=["\']shortlink["\'][^>]*>\s*', '', html, flags=re.I)

    def script_filter(m):
        block = m.group(0)
        if re.search(r'wp-admin/admin-ajax\.php|wp-json|wc-ajax|woocommerce_params|wc_add_to_cart_params|xmlrpc\.php', block, re.I):
            return ''
        return block
    return re.sub(r'<script\b[^>]*>[\s\S]*?</script>', script_filter, html, flags=re.I)

def rewrite_internal_links(html: str, current_file: Path) -> str:
    # Principal pages.
    mapping = {
        SITE + "/": "../../index.html",
        SITE + "/our-services/": "../../our-services/index.html",
        SITE + "/sobre-nosotros/": "../../sobre-nosotros/index.html",
        SITE + "/nuestro-equipo/": "../../nuestro-equipo/index.html",
        SITE + "/contacts/": "../../contacts/index.html",
    }
    for src, dst in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        html = html.replace(src, dst)

    # Services.
    for slug, src in SERVICES.items():
        html = html.replace(src, "../" + slug + "/index.html")

    # Team profiles go to the static team page.
    html = re.sub(
        r'https?://(?:www\.)?valorizeie\.com/cmsms_profile(?:_category)?/[^"\']+/',
        '../../nuestro-equipo/index.html#equipo',
        html,
        flags=re.I,
    )

    # Any surviving normal old-site href gets routed to static home.
    html = re.sub(
        r'(?P<prefix>href=["\'])https?://(?:www\.)?valorizeie\.com/(?!wp-content/|wp-includes/)[^"\']*(?P<q>["\'])',
        r'\g<prefix>../../index.html\g<q>',
        html,
        flags=re.I,
    )
    return html

def localize_html_assets(html: str, source_url: str, current_file: Path) -> str:
    def repl(m):
        full = "https://" + HOST + "/" + m.group("path")
        return localize_asset(full, source_url, current_file)
    html = ASSET_RE.sub(repl, html)

    # Also catch protocol-relative WordPress assets.
    html = html.replace("//valorizeie.com/wp-content/", "https://valorizeie.com/wp-content/")
    html = html.replace("//valorizeie.com/wp-includes/", "https://valorizeie.com/wp-includes/")
    html = ASSET_RE.sub(repl, html)

    # Inline CSS url(...) references.
    return rewrite_css(html, source_url, current_file)

def service_page(slug: str, source_url: str):
    target = ROOT / "services" / slug / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    html = fetch(source_url).decode("utf-8", "replace")
    html = strip_wp_runtime(html)
    html = localize_html_assets(html, source_url, target)
    html = rewrite_internal_links(html, target)

    canonical = f"https://creatiart99.github.io/valorizeie/services/{slug}/"
    html = re.sub(
        r'<link\b[^>]*rel=["\']canonical["\'][^>]*>\s*',
        f'<link rel="canonical" href="{canonical}">\n',
        html,
        flags=re.I,
    )

    # Add our static safety layer.
    if "valorize-overrides.css" not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="../../assets/valorize-overrides.css">\n</head>', 1)
    if "valorize-overrides.js" not in html:
        html = html.replace("</body>", '<script defer src="../../assets/valorize-overrides.js" data-base="../../"></script>\n</body>', 1)

    target.write_text(html, encoding="utf-8")
    print("page", source_url, "->", target.relative_to(ROOT))

def patch_existing_pages():
    pages = {
        ROOT / "index.html": "",
        ROOT / "our-services/index.html": "../",
        ROOT / "sobre-nosotros/index.html": "../",
        ROOT / "nuestro-equipo/index.html": "../",
        ROOT / "contacts/index.html": "../",
    }

    for path, prefix in pages.items():
        html = path.read_text(encoding="utf-8")
        for slug, post_id in SERVICE_POSTS.items():
            replacements = [
                prefix + "our-services/index.html#post-" + post_id,
                "our-services/index.html#post-" + post_id,
                "../our-services/index.html#post-" + post_id,
                "index.html#post-" + post_id,
            ]
            target = prefix + "services/" + slug + "/index.html"
            for old in replacements:
                html = html.replace(old, target)

        # Counter fallback values must not depend on Elementor JS.
        html = re.sub(
            r'(<span class="elementor-counter-number"[^>]*data-to-value="45"[^>]*>)0(</span>)',
            r'\g<1>45\g<2>',
            html,
            flags=re.I,
        )
        html = re.sub(
            r'(<span class="elementor-counter-number"[^>]*data-to-value="1\.5"[^>]*>)0(</span>)',
            r'\g<1>1.5\g<2>',
            html,
            flags=re.I,
        )
        path.write_text(html, encoding="utf-8")

def write_override_js():
    js = r'''(function(){
  const script=document.currentScript;
  const base=script&&script.dataset.base?script.dataset.base:"";
  const routes={
    "/":"index.html",
    "/our-services/":"our-services/index.html",
    "/sobre-nosotros/":"sobre-nosotros/index.html",
    "/nuestro-equipo/":"nuestro-equipo/index.html",
    "/contacts/":"contacts/index.html",
    "/services/captura-del-valor-del-suelo-catastro-e-infraestructura/":"services/captura-del-valor-del-suelo-catastro-e-infraestructura/index.html",
    "/services/analisis-economico-territorial-y-eficiencia-fiscal/":"services/analisis-economico-territorial-y-eficiencia-fiscal/index.html",
    "/services/planeacion-estrategica-del-desarrollo-urbano-y-regional/":"services/planeacion-estrategica-del-desarrollo-urbano-y-regional/index.html",
    "/services/finanzas-publicas-territoriales-y-modelos-de-gestion-financiera/":"services/finanzas-publicas-territoriales-y-modelos-de-gestion-financiera/index.html"
  };
  const local=p=>base+(routes[p]||"index.html");

  function animateCounter(el){
    if(el.dataset.vzAnimated==="1") return;
    el.dataset.vzAnimated="1";
    const from=parseFloat(el.dataset.fromValue||"0");
    const to=parseFloat(el.dataset.toValue||el.textContent||"0");
    const duration=Math.max(350,parseInt(el.dataset.duration||"1200",10));
    const decimals=String(to).includes(".")?String(to).split(".")[1].length:0;
    const start=performance.now();
    function frame(now){
      const t=Math.min(1,(now-start)/duration);
      const eased=1-Math.pow(1-t,3);
      const value=from+(to-from)*eased;
      el.textContent=value.toFixed(decimals);
      if(t<1) requestAnimationFrame(frame);
      else el.textContent=to.toFixed(decimals);
    }
    requestAnimationFrame(frame);
  }

  document.addEventListener("DOMContentLoaded",()=>{
    document.querySelectorAll(".elementor-invisible").forEach(e=>e.classList.remove("elementor-invisible"));

    document.querySelectorAll("a").forEach(a=>{
      const raw=a.getAttribute("href")||"";
      const txt=(a.textContent||"").replace(/\s+/g," ").trim().toLowerCase();
      if(/^https?:\/\/(?:www\.)?valorizeie\.com\//i.test(raw)){
        try{a.href=local(new URL(raw).pathname)}catch(e){a.href=local("/")}
      }
      if(!a.getAttribute("href")||a.getAttribute("href")==="#"){
        if(txt==="inicio")a.href=base+"index.html";
        else if(txt==="servicios")a.href=base+"our-services/index.html";
        else if(txt==="nosotros")a.href=base+"sobre-nosotros/index.html";
        else if(txt==="nuestro equipo")a.href=base+"nuestro-equipo/index.html";
        else if(txt==="contacto"||txt==="contáctanos")a.href=base+"contacts/index.html";
      }
    });

    const counters=[...document.querySelectorAll(".elementor-counter-number[data-to-value]")];
    if("IntersectionObserver" in window){
      const io=new IntersectionObserver(entries=>{
        entries.forEach(entry=>{
          if(entry.isIntersecting){animateCounter(entry.target);io.unobserve(entry.target)}
        })
      },{threshold:.35});
      counters.forEach(c=>io.observe(c));
    }else counters.forEach(animateCounter);

    const team=document.querySelector(".cmsmasters-blog__posts");
    if(team){
      [["cmsms_profile_category-marcos-gomez-calderon","Marcos Gomez Calderon"],["cmsms_profile_category-wilmer-ballen","Wilmer Ballen"],["cmsms_profile_category-alex-smith-araque","Alex Smith Araque"]].forEach(r=>{
        const card=team.querySelector("."+r[0]);
        if(card){
          const t=card.querySelector(".cmsmasters-blog__post-title a,.cmsmasters-blog__post-title,.entry-title a,.entry-title");
          if(t)t.textContent=r[1];
          team.appendChild(card);
        }
      });
    }

    if(!document.querySelector(".vz-whatsapp")){
      const w=document.createElement("a");
      w.className="vz-whatsapp";
      w.href="https://wa.me/573178873523?text=Hola%20Valorize%20I%26E%2C%20quiero%20conversar%20sobre%20un%20proyecto.";
      w.target="_blank";w.rel="noopener";w.setAttribute("aria-label","Hablar por WhatsApp");
      w.innerHTML='<span>WhatsApp</span>';
      document.body.appendChild(w);
    }
  });
})();'''
    (ROOT / "assets/valorize-overrides.js").write_text(js, encoding="utf-8")

def main():
    VENDOR.mkdir(parents=True, exist_ok=True)
    for slug, url in SERVICES.items():
        service_page(slug, url)

    while queued:
        vendor_one(queued.pop(0))

    patch_existing_pages()
    write_override_js()
    print("service migration complete; vendored assets:", len(downloaded))

if __name__ == "__main__":
    main()
