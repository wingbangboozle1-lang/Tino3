/* Tino3 dashboard — vanilla JS charts + Prop 19 calculator. No external deps. */
(function(){
"use strict";
function r10(x){return Math.round(x/10)*10;}
function fmt(x){return "$"+r10(x).toLocaleString("en-US");}
function drawLine(canvasId, series, labels, yLabel){
  var c=document.getElementById(canvasId); if(!c) return;
  var dpr=window.devicePixelRatio||1;
  var w=c.clientWidth, h=c.clientHeight;
  c.width=w*dpr; c.height=h*dpr;
  var ctx=c.getContext("2d"); ctx.scale(dpr,dpr);
  var pad={l:64,r:14,t:14,b:34};
  var all=[]; series.forEach(function(s){s.data.forEach(function(v){all.push(v);});});
  var min=Math.min.apply(null,all), max=Math.max.apply(null,all);
  var span=(max-min)||1; min-=span*0.08; max+=span*0.08;
  function X(i){return pad.l+(w-pad.l-pad.r)*(i/(labels.length-1));}
  function Y(v){return pad.t+(h-pad.t-pad.b)*(1-(v-min)/(max-min));}
  ctx.strokeStyle="#e3e7ee"; ctx.fillStyle="#5b6577"; ctx.font="11px sans-serif";
  for(var g=0;g<=4;g++){var v=min+(max-min)*g/4; var y=Y(v);
    ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();
    ctx.fillText("$"+Math.round(v/1000)+"k",6,y+4);}
  labels.forEach(function(l,i){ctx.fillText(l,X(i)-10,h-10);});
  var colors=["#1f6feb","#0e9f6e","#b45309","#7c3aed"];
  series.forEach(function(s,si){
    ctx.strokeStyle=colors[si%colors.length]; ctx.lineWidth=2.5; ctx.beginPath();
    s.data.forEach(function(v,i){ if(i===0)ctx.moveTo(X(i),Y(v)); else ctx.lineTo(X(i),Y(v)); });
    ctx.stroke();
    ctx.fillStyle=colors[si%colors.length];
    s.data.forEach(function(v,i){ctx.beginPath();ctx.arc(X(i),Y(v),3,0,7);ctx.fill();});
    ctx.fillText(s.name, pad.l+si*150, 12);
  });
  ctx.fillStyle="#5b6577"; ctx.fillText(yLabel||"", pad.l, h-22);
}
function drawBars(canvasId, labels, values, color){
  var c=document.getElementById(canvasId); if(!c) return;
  var dpr=window.devicePixelRatio||1;
  var w=c.clientWidth, h=c.clientHeight;
  c.width=w*dpr; c.height=h*dpr;
  var ctx=c.getContext("2d"); ctx.scale(dpr,dpr);
  var pad={l:64,r:14,t:14,b:34};
  var max=Math.max.apply(null,values)*1.1;
  function Y(v){return pad.t+(h-pad.t-pad.b)*(1-v/max);}
  ctx.strokeStyle="#e3e7ee"; ctx.fillStyle="#5b6577"; ctx.font="11px sans-serif";
  for(var g=0;g<=4;g++){var v=max*g/4; var y=Y(v);
    ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();
    ctx.fillText("$"+Math.round(v/1000)+"k",6,y+4);}
  var bw=(w-pad.l-pad.r)/labels.length*0.6;
  labels.forEach(function(l,i){
    var x=pad.l+(w-pad.l-pad.r)*(i+0.5)/labels.length-bw/2;
    ctx.fillStyle=color||"#1f6feb";
    ctx.fillRect(x,Y(values[i]),bw,h-pad.b-Y(values[i]));
    ctx.fillStyle="#1a2233"; ctx.fillText(fmt(values[i]),x-6,Y(values[i])-6);
    ctx.fillStyle="#5b6577"; ctx.fillText(l,x-6,h-10);
  });
}
function initCharts(){
  var years=[2026,2030,2035,2040,2045,2050];
  var cup=years.map(function(y){return 3100000*Math.pow(1.03,y-2026);});
  var sf=years.map(function(y){return 1800000*Math.pow(1.03,y-2026);});
  drawLine("chartValues",[{name:"Cupertino FMV",data:cup},{name:"SF FMV",data:sf}],years.map(String),"Market value (3%/yr scenario)");
  var inv10=2914000*Math.pow(1.07,10), inv20=2914000*Math.pow(1.07,20);
  var hold10=3100000*Math.pow(1.03,10), hold20=3100000*Math.pow(1.03,20);
  drawBars("chartSellHold",["Sell+Invest 10y","Hold House 10y","Sell+Invest 20y","Hold House 20y"],[inv10,hold10,inv20,hold20],"#0e9f6e");
  var taxMove=27450, taxRent=41390, taxNow=7210;
  drawBars("chartTax",["Current","Move-in","Rent/Full"],[taxNow,taxMove,taxRent],"#b45309");
}
function initCalc(){
  var fmv=document.getElementById("calcFmv"), cap=document.getElementById("calcCap"),
      rate=document.getElementById("calcRate"), mode=document.getElementById("calcMode"),
      out=document.getElementById("calcOut");
  if(!fmv) return;
  function run(){
    var F=parseFloat(fmv.value)||0, C=parseFloat(cap.value)||0, R=(parseFloat(rate.value)||0)/100;
    var assessed = mode.value==="movein" ? Math.max(F-C,0) : F;
    // If FMV <= FBYV+cap, assessed stays at FBYV; calculator uses simplified FMV-cap floor with note.
    out.innerHTML="New assessed value: <strong>"+fmt(assessed)+"</strong> &nbsp;|&nbsp; Est. annual tax: <strong>"+fmt(assessed*R)+"</strong>"+
      (mode.value==="movein" ? "<br><span class='small'>Simplified: FMV − cap. Exact result also needs the parent's factored base-year value (FBYV). See Taxes page.</span>" : "");
  }
  [fmv,cap,rate,mode].forEach(function(el){el.addEventListener("input",run);el.addEventListener("change",run);});
  run();
}
document.addEventListener("DOMContentLoaded",function(){initCharts();initCalc();});
window.addEventListener("resize",initCharts);
})();
