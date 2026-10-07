(function(){
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
})();