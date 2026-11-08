import { registar } from "../motor.js";

// Atmosfera «O medo da guerra das máquinas» (STAR-42, protótipo aprovado no STAR-51): HUD vermelho,
// glitch e scanlines que crescem com o scroll (--g), contagem que o leitor pode parar e mosaico que se parte.
// Sem biblioteca: CSS + JS próprio. Com movimento reduzido o estado fica estático e legível.
registar("atmosfera:guerra-maquinas", ({ el, reduzido }) => {
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const root=el.closest('.ag-raiz'), S=root.style;
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const movel=()=>innerWidth<900;
let pausado=reduzido, corte=1, corteAlvo=1, gBase=0, gShow=-1, jx=0, jy=0, tJ=0, valor=10, parado=false;
if(reduzido) root.classList.add('ag-estatico');

/* ---------- HUD: marcas e contagem ---------- */
(()=>{let h='';for(let i=0;i<60;i++){const a=i/60*Math.PI*2,r1=i%5?170:164,r2=178;h+=`<line x1="${(200+r1*Math.sin(a)).toFixed(1)}" y1="${(200-r1*Math.cos(a)).toFixed(1)}" x2="${(200+r2*Math.sin(a)).toFixed(1)}" y2="${(200-r2*Math.cos(a)).toFixed(1)}"/>`}$('#ag-ticks').innerHTML=h})();
const cntEl=$('#ag-cnt'), hud=$('#ag-hud'), pst=$('#ag-pst');
const pad=n=>String(n).padStart(2,'0');
function pintaContagem(v){
  cntEl.textContent=pad(Math.max(0,Math.round(v)));
  hud.classList.toggle('ag-zero',!parado&&Math.round(v)<=0);
  const n=Math.round(v);
  pst.textContent=parado?`contagem parada em ${pad(n)}: o leitor interrompeu`:(n<=0?'contagem em 00: ninguém interveio':`contagem a correr: ${pad(n)}`);
}
$('#ag-para').addEventListener('click',()=>{parado=!parado;hud.classList.toggle('ag-parado',parado);$('#ag-para').textContent=parado?'Retomar a contagem':'Parar a contagem';pintaContagem(valor)});

/* ---------- mosaico 14 x 8 (112 células que se partem e se recompõem) ---------- */
const COL=14, LIN=8;
function rnd(i){const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x)}
function montaMosaico(el){
  const cel=[];
  for(let r=0;r<LIN;r++)for(let c=0;c<COL;c++){
    const i=document.createElement('i'), k=r*COL+c;
    i.style.cssText=`left:${c/COL*100}%;top:${r/LIN*100}%;width:${100/COL}%;height:${100/LIN}%;background-size:${COL*100}% ${LIN*100}%;background-position:${c/(COL-1)*100}% ${r/(LIN-1)*100}%`;
    const a=rnd(k)*6.283, d=1.2+rnd(k+200)*4.8;
    cel.push({el:i,dx:Math.cos(a)*d*100,dy:Math.sin(a)*d*80+(rnd(k+7)-.3)*160,rot:(rnd(k+99)-.5)*220,sc:.35+rnd(k+51)*.4});
    el.appendChild(i);
  }
  return d=>{ d=clamp(d); for(const c of cel){c.el.style.transform=d<.002?'':`translate(${(c.dx*d).toFixed(0)}%,${(c.dy*d).toFixed(0)}%) rotate(${(c.rot*d).toFixed(1)}deg) scale(${(1-(1-c.sc)*d).toFixed(2)})`;c.el.style.opacity=(1-d*.35).toFixed(2)} };
}
const setMos=montaMosaico($('#ag-mos')), setA=montaMosaico($('#ag-mosA')), setB=montaMosaico($('#ag-mosB'));
setA(0); setB(.42);
let dMos=-1;
function mosaico(p){
  const d=p<.5?p/.5:(1-p)/.5, dq=Math.round(clamp(d)*80)/80;
  if(dq!==dMos){dMos=dq;setMos(dq);$('#ag-c1').classList.toggle('ag-on',dq<.12);$('#ag-c2').classList.toggle('ag-on',dq>=.12)}
}

/* ---------- g: 0 → 1 → 0 com o scroll; o botão «interromper» baixa de facto ---------- */
let anc=[];
function medeAncoras(){
  const y=el=>el.getBoundingClientRect().top+scrollY, h=el=>el.offsetHeight, vh=innerHeight;
  const a1=$('#ag-ato1'), a2=$('#ag-ato2'), a3=$('#ag-ato3');
  anc=[[0,0],[y(a1),.10],[y(a1)+h(a1)*.5,.38],[y(a2),.52],[y(a2)+h(a2)*.5,1],[y(a2)+h(a2)-vh,.8],[y(a3),.62],[y($('.ag-fecho'))-vh*.6,0],[1e9,0]];
}
function gDoScroll(){
  const s=scrollY;
  for(let i=1;i<anc.length;i++){ if(s<=anc[i][0]){const [x0,g0]=anc[i-1],[x1,g1]=anc[i];return g0+(g1-g0)*clamp((s-x0)/Math.max(1,x1-x0))} }
  return 0;
}
const topoSite=()=>movel()?66:76;
function progresso(el){const r=el.getBoundingClientRect(),off=topoSite();return clamp((off-r.top)/Math.max(1,el.offsetHeight-(innerHeight-off)))}
function leScroll(P1,P2){
  gBase=reduzido?.15:gDoScroll();
  const p1=reduzido?1:(P1===undefined?progresso($('#ag-ato1')):P1);
  if(reduzido){ valor=4; parado=true; hud.classList.add('ag-parado'); $('#ag-para').textContent='Contagem parada'; $('#ag-para').disabled=true }
  else if(!parado) valor=10-10*clamp((p1-.1)/.7);
  pintaContagem(valor);
  if(!reduzido) mosaico(P2===undefined?progresso($('#ag-ato2')):P2);
  S.setProperty('--gy',(scrollY*.35%46).toFixed(1)+'px');
}
function aplicaG(t){
  const g=clamp(gBase*corte);
  if(Math.abs(g-gShow)>.004){gShow=g;S.setProperty('--g',g.toFixed(3));$('#ag-gv').textContent=Math.round(g*100)}
  if(!reduzido&&g>.04&&t-tJ>(110-g*50)){tJ=t;jx=(Math.random()*2-1);jy=(Math.random()*2-1);if(Math.random()<.2){jx=jx<0?-1:1}S.setProperty('--jx',jx.toFixed(2));S.setProperty('--jy',jy.toFixed(2))}
  else if(g<=.04&&jx!==0){jx=jy=0;S.setProperty('--jx','0');S.setProperty('--jy','0')}
  const f=$('#ag-faixa'); f.style.transform=`translate3d(0,${((t*.22)%(innerHeight+120)-60).toFixed(0)}px,0)`;
}

/* ---------- interromper / rearmar ---------- */
const reg=$('#ag-registro');
$('#ag-interromper').addEventListener('click',()=>{
  corteAlvo=0; const r=$('#ag-f-resp').value.trim()||'sem responsável nomeado';
  reg.textContent=`Sistema interrompido por: ${r}. Alarme em 0 %. Só volta se alguém rearmar.`;
  $('#ag-interromper').textContent='Sistema interrompido'; if(pausado||reduzido){corte=0;aplicaG(performance.now())}
});
$('#ag-rearmar').addEventListener('click',()=>{corteAlvo=1;reg.textContent='Alarme rearmado: o glitch volta à intensidade do ponto da página.';$('#ag-interromper').textContent='Interromper o sistema'; if(pausado||reduzido){corte=1;aplicaG(performance.now())}});

/* ---------- sinais: um aberto de cada vez ---------- */
$$('#ag-sinais details').forEach(d=>d.addEventListener('toggle',()=>{ if(d.open) $$('#ag-sinais details').forEach(o=>{if(o!==d)o.open=false}) }));

/* ---------- a moldura reage ao cursor (borda e superfície mais perto acendem) ---------- */
let hudEls=[], PX=-999, PY=-999;
const mira=$('#ag-mira'); let mx=innerWidth/2, my=innerHeight/2;
addEventListener('pointermove',e=>{ if(e.pointerType==='touch') return; PX=e.clientX; PY=e.clientY; const t=e.target; mira.style.visibility=(t&&t.closest&&t.closest('.ag-veu,.ag-painel,.ag-sinais,.ag-hud,.ag-fecho,.ag-hero>div'))?'hidden':''; if(pausado) luz() },{passive:true});
function luz(rs){
  const vh=innerHeight; rs=rs||hudEls.map(e=>e.getBoundingClientRect());
  for(let i=0;i<hudEls.length;i++){
    const el=hudEls[i], r=rs[i]; if(r.bottom<-200||r.top>vh+200) continue;
    const ex=Math.max(r.left-PX,0,PX-r.right), ey=Math.max(r.top-PY,0,PY-r.bottom), d=Math.hypot(ex,ey);
    el.style.setProperty('--lx',(PX-r.left).toFixed(0)+'px'); el.style.setProperty('--ly',(PY-r.top).toFixed(0)+'px');
    el.style.setProperty('--li',Math.pow(Math.max(0,1-d/360),.9).toFixed(2));
  }
}

/* ---------- loop, pausa, visibilidade ---------- */
let raf=0, tl=0, ag=false; const A1=$('#ag-ato1'), A2=$('#ag-ato2');
function frame(t){
  raf=0; if(pausado||document.hidden) return;
  const rs=((tl&1)===0)?hudEls.map(e=>e.getBoundingClientRect()):null, P1=progresso(A1), P2=progresso(A2);
  corte+=(corteAlvo-corte)*.06; if(Math.abs(corteAlvo-corte)<.003) corte=corteAlvo;
  leScroll(P1,P2); aplicaG(t);
  mx+=(PX-mx)*.2; my+=(PY-my)*.2; if(PX>-900) mira.style.transform=`translate3d(${mx.toFixed(1)}px,${my.toFixed(1)}px,0)`;
  if(rs) luz(rs); tl++;
  raf=requestAnimationFrame(frame);
}
function liga(){ if(!raf&&!pausado&&!document.hidden) raf=requestAnimationFrame(frame) }
function unico(){ if(ag) return; ag=true; requestAnimationFrame(()=>{ag=false; if(pausado){leScroll();aplicaG(performance.now());luz()}}) }
addEventListener('scroll',unico,{passive:true});
document.addEventListener('visibilitychange',()=>{ if(document.hidden){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
const bt=$('#ag-pausa');
function rotulo(){bt.textContent=reduzido?'movimento pausado':(pausado?'retomar movimento':'pausar movimento');bt.setAttribute('aria-pressed',String(pausado));root.classList.toggle('ag-pausado',pausado)}
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado){ if(raf){cancelAnimationFrame(raf);raf=0}; S.setProperty('--jx','0');S.setProperty('--jy','0'); } else liga() });
rotulo();
function inicia(){hudEls=$$('.ag-hud-el');medeAncoras();leScroll();aplicaG(performance.now());luz()}
addEventListener('resize',()=>{medeAncoras();leScroll();aplicaG(performance.now())});
addEventListener('load',()=>{medeAncoras();leScroll()});
inicia(); if(!reduzido) liga();
if(reduzido){ corte=corteAlvo=1 }
});
