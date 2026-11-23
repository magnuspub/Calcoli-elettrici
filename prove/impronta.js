// Impronta dei risultati di Calcoli_elettrici.html: eseguita nella pagina da prova.py dopo l'apertura di un caso.
// Restituisce, per ogni modulo richiesto, i testi mostrati (riquadri, verifiche, tabelle, note), i valori interni
// a piena precisione, l'aspetto dei grafici e il contenuto delle esportazioni. Non modifica la pagina.
(mods)=>{
  // dalla 0.2.1 i grafici di fusibili e interruttori stanno nel modulo «Coordinamento protezioni»: si raccoglie anche quello
  if((mods.indexOf('modFUS')>=0||mods.indexOf('modCB')>=0)&&mods.indexOf('modCOO')<0) mods=mods.concat(['modCOO']);
  const h=s=>{ let a=2166136261; for(let i=0;i<s.length;i++){ a^=s.charCodeAt(i); a=Math.imul(a,16777619); } return (a>>>0).toString(16).padStart(8,"0"); };
  const T=e=>{ if(!e) return null; const c=e.cloneNode(true); c.querySelectorAll(".tip,select,script,style,button").forEach(x=>x.remove()); return c.textContent.replace(/\s+/g," ").trim(); };
  const vis=e=>e.offsetParent!==null;
  // riassunto di un oggetto: numeri a 10 cifre, vettori lunghi ridotti a numero di elementi, somma e somma dei logaritmi
  const dig=(o,d,seen)=>{
    if(o==null) return null; const t=typeof o;
    if(t==="number") return Number.isFinite(o)?+o.toPrecision(10):String(o);
    if(t==="string") return o.length>90?o.slice(0,50)+"…#"+h(o):o;
    if(t==="boolean") return o; if(t==="function") return undefined;
    if(typeof Node!=="undefined"&&o instanceof Node) return undefined;
    if(seen.has(o)) return "(già visto)"; seen.add(o);
    if(o instanceof Set) o=[...o];
    if(Array.isArray(o)){
      if(o.length>8&&o.every(x=>typeof x==="number")){ let s=0,l=0; o.forEach(x=>{ if(Number.isFinite(x)){ s+=x; l+=Math.log(Math.abs(x)+1e-300); } }); return {n:o.length,somma:+s.toPrecision(10),log:+l.toPrecision(10)}; }
      return d>8?"[…]":o.map(x=>{ const v=dig(x,d+1,seen); return v===undefined?null:v; });
    }
    if(d>8) return "{…}"; const r={}; Object.keys(o).sort().forEach(k=>{ const v=dig(o[k],d+1,seen); if(v!==undefined) r[k]=v; }); return r;
  };
  const D=o=>dig(o,0,new WeakSet());
  const stati={modCC:()=>typeof CC_ST!=="undefined"?CC_ST:null, modFUS:()=>typeof FUS_ST!=="undefined"?FUS_ST:null, modCB:()=>typeof CB_ST!=="undefined"?CB_ST:null,
    modPMT:()=>typeof PMT_ST!=="undefined"?PMT_ST:null, modCOO:()=>typeof COO_ST!=="undefined"?COO_ST:null, modLP:()=>window.LPUI&&LPUI.results?LPUI.results():null};
  const xls={modCC:"xlsCC",modFUS:"xlsFUS",modCB:"xlsCB",modPMT:"xlsPMT",modVK:"xlsVK",modMT:"xlsMT",modREL:"xlsREL"};
  const out={};
  mods.forEach(m=>{
    const r=document.getElementById(m); if(!r){ out[m]={mancante:true}; return; }
    const o={};
    o.riquadri=[...r.querySelectorAll(".kpi")].filter(vis).map(T);
    o.verifiche=[...r.querySelectorAll(".check")].filter(vis).map(c=>T(c.querySelector(".lbl"))+" → "+T(c.querySelector(".badge")));
    o.tabelle=[...r.querySelectorAll("table")].filter(vis).map(T);
    o.note=[...r.querySelectorAll(".warnrow,[data-o],.ttlrow,#mt_verdict,#pm_copyMsg,#pillFault")].filter(vis).map(T).filter(x=>x&&x!=="—");
    try{ const s=stati[m]&&stati[m](); if(s) o.valori=D(s); }catch(e){ o.valori="errore: "+e.message; }
    // aspetto: legende e geometria dei grafici (dipende anche dalla larghezza della finestra)
    o.aspetto={legende:[...r.querySelectorAll("[id$=legend],[id^=pm_leg]")].filter(vis).map(T),
      grafici:[...r.querySelectorAll("svg")].filter(s=>vis(s)&&s.getBoundingClientRect().width>150).map(s=>{
        const geo=[...s.querySelectorAll("path,polyline,polygon")].map(e=>(e.getAttribute("d")||e.getAttribute("points")||"")).join("|");
        const tx=[...s.querySelectorAll("text")].map(t=>t.textContent).join("|");
        let p=s.parentElement; while(p&&!p.id) p=p.parentElement; return (p?p.id:"")+" linee "+h(geo)+" scritte "+h(tx); })};
    // esportazioni: foglio Excel (celle e formule, senza la riga con data e versione) e contenuto del PDF
    o.esportazioni={};
    try{ if(xls[m]&&typeof window[xls[m]]==="function"){ const S=window[xls[m]](); o.esportazioni.excel=h(JSON.stringify(S.rows.filter((row,i)=>!(i<3&&row[0]&&row[0].s===7)).map(row=>row.map(c=>c?(c.f!=null?"="+c.f:c.v):"")))); o.esportazioni.righe=S.rows.length;
        (S.more||[]).forEach(Q=>{ o.esportazioni["excel · foglio "+Q.name]=h(JSON.stringify(Q.rows.filter((row,i)=>!(i<3&&row[0]&&row[0].s===7)).map(row=>row.map(c=>c?(c.f!=null?"="+c.f:c.v):"")))); }); } }catch(e){ o.esportazioni.excel="errore: "+e.message; }
    try{ if(typeof collectModule==="function"&&m!=="modLP") o.esportazioni.pdf=h(JSON.stringify(collectModule(m))); }catch(e){ o.esportazioni.pdf="errore: "+e.message; }
    out[m]=o;
  });
  return out;
}
