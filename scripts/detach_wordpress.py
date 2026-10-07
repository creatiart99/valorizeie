#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGES={
 "index.html":("", ""),
 "our-services/index.html":("../","our-services/"),
 "sobre-nosotros/index.html":("../","sobre-nosotros/"),
 "nuestro-equipo/index.html":("../","nuestro-equipo/"),
 "contacts/index.html":("../","contacts/"),
}
GH="https://creatiart99.github.io/valorizeie/"

SERVICE_MAP={
 "https://valorizeie.com/services/captura-del-valor-del-suelo-catastro-e-infraestructura/":"our-services/index.html#post-40278",
 "https://valorizeie.com/services/analisis-economico-territorial-y-eficiencia-fiscal/":"our-services/index.html#post-40114",
 "https://valorizeie.com/services/planeacion-estrategica-del-desarrollo-urbano-y-regional/":"our-services/index.html#post-40277",
 "https://valorizeie.com/services/finanzas-publicas-territoriales-y-modelos-de-gestion-financiera/":"our-services/index.html#post-41418",
}
PROFILE_URLS=[
 "https://valorizeie.com/cmsms_profile/wilmer-ballen/",
 "https://valorizeie.com/cmsms_profile/alex-smith-araque/",
 "https://valorizeie.com/cmsms_profile/marcos-gomez-calderon/",
 "https://valorizeie.com/cmsms_profile_category/wilmer-ballen/",
 "https://valorizeie.com/cmsms_profile_category/alex-smith-araque/",
 "https://valorizeie.com/cmsms_profile_category/marcos-gomez-calderon/",
]

def clean(html,prefix,canon):
    for src,dst in SERVICE_MAP.items():
        html=html.replace(src,prefix+dst)
    for src in PROFILE_URLS:
        html=html.replace(src,prefix+"nuestro-equipo/index.html#equipo")
    html=html.replace("https://valorizeie.com/sobre-nosotros/",prefix+"sobre-nosotros/index.html")

    html=re.sub(r'<link\b[^>]*(?:feed/|comments/feed/|wp-json|xmlrpc\.php|api\.w\.org)[^>]*>\s*','',html,flags=re.I)
    html=re.sub(r'<meta\b[^>]*name=["\']generator["\'][^>]*(?:WordPress|WooCommerce|Elementor)[^>]*>\s*','',html,flags=re.I)
    html=re.sub(r'<link\b[^>]*rel=["\']shortlink["\'][^>]*>\s*','',html,flags=re.I)
    html=re.sub(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>\s*',f'<link rel="canonical" href="{GH}{canon}">\n',html,flags=re.I)

    html=re.sub(r'<script\b[^>]*(?:id=["\'][^"\']*(?:woocommerce|wc-|wc_)[^"\']*["\']|src=["\'][^"\']*woocommerce[^"\']*["\'])[^>]*>[\s\S]*?</script>\s*','',html,flags=re.I)

    def drop_wp_script(m):
        b=m.group(0)
        return '' if re.search(r'wp-admin/admin-ajax\.php|wp-json|wc-ajax|xmlrpc\.php',b,re.I) else b
    html=re.sub(r'<script\b[^>]*>[\s\S]*?</script>',drop_wp_script,html,flags=re.I)

    html=re.sub(r'https?://valorizeie\.com/(?:feed/|comments/feed/|wp-json[^"\'<>\\\s)]*|wp-admin[^"\'<>\\\s)]*|xmlrpc\.php[^"\'<>\\\s)]*|cart/? )',prefix+"index.html",html,flags=re.I)
    html=html.replace('/wp-admin/admin-ajax.php','').replace('/?wc-ajax=%%endpoint%%','')
    html=re.sub(r'https?://valorizeie\.com/(?!wp-content/|wp-includes/)[^"\'<>\\\s)]*',prefix+"index.html",html,flags=re.I)
    html=html.replace('https:\\/\\/valorizeie.com\\/','https:\\/\\/creatiart99.github.io\\/valorizeie\\/')
    html=html.replace('/wp-json/','')

    html=re.sub(r'<main id="main"', '<main id="main" data-static-site="true"', html, count=1, flags=re.I)
    if canon=="nuestro-equipo/" and 'id="equipo"' not in html:
        p=html.find('cmsmasters-blog__posts')
        if p>0:
            s=html.rfind('<div',0,p)
            if s>=0:
                html=html[:s]+html[s:].replace('<div','<div id="equipo"',1)
    return html

for rel,(prefix,canon) in PAGES.items():
    p=ROOT/rel
    p.write_text(clean(p.read_text(encoding="utf-8"),prefix,canon),encoding="utf-8")

js=r'''(function(){
 const s=document.currentScript,base=s&&s.dataset.base?s.dataset.base:"";
 const map={
  "/":"index.html","/our-services/":"our-services/index.html","/sobre-nosotros/":"sobre-nosotros/index.html",
  "/nuestro-equipo/":"nuestro-equipo/index.html","/contacts/":"contacts/index.html",
  "/services/captura-del-valor-del-suelo-catastro-e-infraestructura/":"our-services/index.html#post-40278",
  "/services/analisis-economico-territorial-y-eficiencia-fiscal/":"our-services/index.html#post-40114",
  "/services/planeacion-estrategica-del-desarrollo-urbano-y-regional/":"our-services/index.html#post-40277",
  "/services/finanzas-publicas-territoriales-y-modelos-de-gestion-financiera/":"our-services/index.html#post-41418",
  "/cmsms_profile/wilmer-ballen/":"nuestro-equipo/index.html#equipo",
  "/cmsms_profile/alex-smith-araque/":"nuestro-equipo/index.html#equipo",
  "/cmsms_profile/marcos-gomez-calderon/":"nuestro-equipo/index.html#equipo"
 };
 const local=p=>base+(map[p]||"index.html");
 document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".elementor-invisible").forEach(e=>e.classList.remove("elementor-invisible"));
  document.querySelectorAll("a").forEach(a=>{
   const raw=a.getAttribute("href")||"",txt=(a.textContent||"").replace(/\s+/g," ").trim().toLowerCase();
   if(/^https?:\/\/(?:www\.)?valorizeie\.com\//i.test(raw)){try{a.href=local(new URL(raw).pathname)}catch(e){a.href=local("/")}}
   if(!a.getAttribute("href")||a.getAttribute("href")==="#"){
    if(txt==="inicio")a.href=base+"index.html";
    else if(txt==="servicios")a.href=base+"our-services/index.html";
    else if(txt==="nosotros")a.href=base+"sobre-nosotros/index.html";
    else if(txt==="nuestro equipo")a.href=base+"nuestro-equipo/index.html";
    else if(txt==="contacto"||txt==="contáctanos"||txt==="contácto")a.href=base+"contacts/index.html";
   }
  });
  document.querySelectorAll(".elementor-element-a6692a5 a").forEach(a=>{a.href=base+"contacts/index.html";const t=a.querySelector(".elementor-widget-cmsmasters-button__text");if(t)t.textContent="Contacto"});
  const team=document.querySelector(".cmsmasters-blog__posts");
  if(team)[["cmsms_profile_category-marcos-gomez-calderon","Marcos Gomez Calderon"],["cmsms_profile_category-wilmer-ballen","Wilmer Ballen"],["cmsms_profile_category-alex-smith-araque","Alex Smith Araque"]].forEach(r=>{const card=team.querySelector("."+r[0]);if(card){const t=card.querySelector(".cmsmasters-blog__post-title a,.cmsmasters-blog__post-title,.entry-title a,.entry-title");if(t)t.textContent=r[1];team.appendChild(card)}});
  if(!document.querySelector(".vz-whatsapp")){const w=document.createElement("a");w.className="vz-whatsapp";w.href="https://wa.me/573178873523?text=Hola%20Valorize%20I%26E%2C%20quiero%20conversar%20sobre%20un%20proyecto.";w.target="_blank";w.rel="noopener";w.innerHTML="<span>WhatsApp</span>";document.body.appendChild(w)}
 });
})();'''
(ROOT/"assets/valorize-overrides.js").write_text(js,encoding="utf-8")
print("detached")
