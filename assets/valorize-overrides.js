(function(){
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
})();