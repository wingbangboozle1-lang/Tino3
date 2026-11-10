// Tino3 — inheritance decision site logic. No external deps.
const fmt$ = n => n==null||isNaN(n) ? "—" : "$" + Math.round(n/10)*10 .toLocaleString("en-US");
const fmt$0 = n => n==null||isNaN(n) ? "—" : "$" + Math.round(n).toLocaleString("en-US");
const round10 = n => Math.round(n/10)*10;
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

// Modelled projections. All assumptions explicit; see methodology page.
function projectProperty(baseMarket, baseAssessed, effRate, years, growth){
  const out=[]; let m=baseMarket, a=baseAssessed;
  for(let i=0;i<years.length;i++){
    const y=years[i];
    if(i>0){ m=m*(1+growth); a=a*1.02; } // Prop 13 cap 2%
    out.push({year:y, market:round10(m), assessed:round10(a), tax:round10(a*effRate)});
  }
  return out;
}
// Prop 19 reassessment at transfer year T
function prop19(market, assessed, cap, effRate, occupy){
  const spread = market - assessed;
  if(!occupy) return {newAssessed:round10(market), tax:round10(market*effRate), note:"Full reassessment (not primary residence)"};
  if(spread<=cap) return {newAssessed:round10(assessed), tax:round10(assessed*effRate), note:"Full exclusion (within cap)"};
  const excess = market - (assessed+cap);
  const na = assessed+excess;
  return {newAssessed:round10(na), tax:round10(na*effRate), note:"Partial reassessment (excess over cap)"};
}
function loadJSON(path){return fetch(path).then(r=>{if(!r.ok)throw new Error(path);return r.json();});}
document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll("[data-year]").forEach(el=>el.textContent=new Date().getFullYear());
});
