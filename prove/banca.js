// Impronta della banca dati di Calcoli_elettrici.html: tabelle e curve grezze, più le curve calcolate di un interruttore
// per serie e di tre fusibili per famiglia. Eseguita nella pagina da prova.py e dall'ambiente di manutenzione.
async()=>{
  const h=s=>{ let a=2166136261; for(let i=0;i<s.length;i++){ a^=s.charCodeAt(i); a=Math.imul(a,16777619); } return (a>>>0).toString(16).padStart(8,"0"); };
  const sum=c=>{ if(!c) return null; let s=0,l=0; c.forEach(x=>{ if(Number.isFinite(x)){ s+=x; l+=Math.log(Math.abs(x)+1e-300); } }); return [c.length,+s.toPrecision(10),+l.toPrecision(10)]; };
  const out={tabelle:{}};
  // dalla 0.2.14 fusibili e interruttori sono esclusi all'apertura: per provare le curve vanno inclusi
  ["onFus","onCb"].forEach(id=>{ const e=document.getElementById(id); if(e&&!e.checked){ e.checked=true; } }); if(typeof recompute==="function") recompute();
  const T={MAT,CABLE_X,CABLE_K,GRID_PRESETS,TR_TYP,INRUSH,UTP_TABLE,FMT_TR,LP_EX,FUS_DB,CB_DB};
  ["TR_WTH","PMT_CUR","PMT_MOD","VG"].forEach(k=>{ try{ T[k]=eval(k); }catch(e){} });
  Object.keys(T).forEach(k=>{ out.tabelle[k]=h(JSON.stringify(T[k])); });
  out.numero={fusibili:FUS_DB.p.length,interruttori:CB_DB.p.length,serie:CB_DB.s.length};
  // fusibili: primo, centrale e ultimo di ogni famiglia
  out.fusibili={}; const fam={}; FUS_DB.p.forEach((p,i)=>{ (fam[p[1]]=fam[p[1]]||[]).push(i); });
  Object.keys(fam).forEach(g=>{ const a=fam[g]; [a[0],a[a.length>>1],a[a.length-1]].forEach(i=>{ document.getElementById("fu_grpA").value=FUS_DB.p[i][1]; fusFillSizes("fu_grpA","fu_selA",0); document.getElementById("fu_selA").value=i; const f=fusGet("fu_selA");
    out.fusibili[f.type]={In:f.In,Un:f.Un,Icn:f.Icn,t:sum(f.t),l:sum(f.l),i:sum(f.i)}; }); });
  // interruttori: il centrale e l'ultimo di ogni serie, con le regolazioni proposte
  out.interruttori={}; const ser={}; CB_DB.p.forEach((p,i)=>{ const k=CB_DB.g[p[1]][0]; (ser[k]=ser[k]||[]).push(i); });
  for(const k of Object.keys(ser)){ const a=ser[k]; for(const i of [a[a.length>>1],a[a.length-1]]){ const p=CB_DB.p[i], g=CB_DB.g[p[1]];
      allSetCb("A",{tipo:p[0],serie:CB_DB.s[g[0]][1],esecuzione:cbFamTxt(g)},{ok:0,skip:[],miss:[]}); computeCb(); const b=CB_ST.res[0].b;
      out.interruttori[k+" · "+p[0]]={nome:cbName(b),Ir:b.Ir,Ii:b.Ii,Icu:b.Icu,Un:b.Un,max:sum(b.max),min:sum(b.min),d:b.d?sum(b.d.c):null,e:b.e?sum(b.e.c):null}; } }
  return out;
}
