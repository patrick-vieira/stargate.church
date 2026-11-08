import { registar } from "../motor.js";

// Atmosfera «Leis, robôs e livros» (STAR-45, protótipo STAR-51/05).
// Mesa de papel com lâmpada que segue o cursor, livro cuja página vira em 3D ao rolar (CSS 3D),
// tipos móveis que se alinham, regras originais que se riscam e se reescrevem, mapa de rede e oficina local.
// Tudo local e sem rede. Com movimento reduzido: modo linear, estado final, sem loop.
registar("atmosfera:leis-robos-livros", ({ el, reduzido }) => {
const root=el.closest('.lr-raiz');
const $=(s,r=root)=>r.querySelector(s), $$=(s,r=root)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const movel=()=>innerWidth<900;
const TOPO=76; /* altura do cabeçalho do site: o livro cola-se abaixo dele */
let pausado=reduzido, linear=false;
if(reduzido) root.classList.add('lr-estatico');
function modo(){ linear=reduzido||movel(); root.classList.toggle('lr-linear',linear); }
modo();

/* ---------- o mapa de rede (14 nós, 3 grandes) ---------- */
const svg=$('#lr-mapa'), NS=svg.namespaceURI;
const G=[[130,150],[300,70],[390,215]];
const P=[[60,60],[170,30],[225,95],[90,235],[170,265],[240,200],[350,25],[450,95],[470,170],[330,150],[440,270]];
const GRUPO=[0,0,0,0,0,0,1,1,2,1,2];
const lig=[], nos=[];
(function(){
  const s=document.createElementNS(NS,'g'); svg.appendChild(s);
  function path(a,b){const e=document.createElementNS(NS,'path');e.setAttribute('d',`M${a[0]} ${a[1]}L${b[0]} ${b[1]}`);e.setAttribute('pathLength','1');e.setAttribute('class','lr-lig');s.appendChild(e);lig.push(e)}
  path(G[0],G[1]);path(G[1],G[2]);path(G[0],G[2]);
  P.forEach((p,i)=>path(G[GRUPO[i]],p));
  function no(p,g){const c=document.createElementNS(NS,'circle');c.setAttribute('cx',p[0]);c.setAttribute('cy',p[1]);c.setAttribute('r',g?15:7);c.setAttribute('class','lr-no'+(g?' lr-g':''));s.appendChild(c);nos.push({el:c,x:p[0],y:p[1]})}
  P.forEach(p=>no(p,0)); G.forEach(p=>no(p,1));
})();
function desenhaRede(q){ lig.forEach((l,i)=>{const k=clamp(q*1.6-(i/lig.length)*.6);l.style.setProperty('--d',(1-k).toFixed(3))}) }

/* ---------- tipos móveis ---------- */
const tipos=$$('.lr-tipo'), TD=[[-130,-50,-14],[100,-55,11],[-80,50,13],[140,40,-9]];
function alinha(q){ const e=linear?.45:1; tipos.forEach((t,i)=>{const d=TD[i],k=1-q;t.style.transform=`translate(${(d[0]*k*e).toFixed(1)}px,${(d[1]*k*e).toFixed(1)}px) rotate(${(d[2]*k).toFixed(1)}deg)`}) }

/* ---------- regras que se reescrevem ---------- */
const rgs=$$('.lr-rg').map(r=>({el:r,risco:$('.lr-risco',r),ok:$('.lr-ok',r),res:$('.lr-res',r),txt:$('.lr-nova .lr-sr',r).textContent,n:-1}));
function reescreve(q){
  rgs.forEach((r,i)=>{
    const u=clamp(q*3-i), k=clamp(u/.4), n=Math.round(clamp((u-.4)/.6)*r.txt.length);
    r.risco.style.setProperty('--k',k.toFixed(3));
    if(n!==r.n){r.n=n;r.ok.textContent=r.txt.slice(0,n);r.res.textContent=r.txt.slice(n)}
  });
}

/* ---------- o livro: progresso, páginas e visibilidade ---------- */
const pista=$('#lr-pista'), livro=$('#lr-livro'), l1=$('#lr-l1'), l2=$('#lr-l2');
const faces={tipos:$('#lr-pg-tipos'),f1:$('#lr-f1'),v1:$('#lr-v1'),f2:$('#lr-f2'),v2:$('#lr-v2'),a3:$('#lr-pg-ato3')};
const ease=t=>t*t*(3-2*t);
let pAtual=-1;
function progresso(){
  const r=pista.getBoundingClientRect(); return clamp((TOPO-r.top)/Math.max(1,pista.offsetHeight-innerHeight+TOPO));
}
function visib(r1,r2){
  const v=(e,on)=>e.classList.toggle('lr-off',!on);
  v(faces.tipos,r1<172); v(faces.f1,r1<90); v(faces.v1,r1>=90&&r2<90);
  v(faces.f2,r1>2&&r2<90); v(faces.v2,r2>=90); v(faces.a3,r2>2);
}
/* STAR-45 (retoques): a capa do livro fechado abre aos ~8 % do scroll da página; estática (fechada) no reduzido e no modo linear */
const capa=$('#lr-capa');
function capaAtualiza(){
  if(!capa||reduzido||linear) return;
  const h=Math.max(1,document.documentElement.scrollHeight-innerHeight);
  capa.style.setProperty('--c',(-ease(clamp(scrollY/(h*.08)))*165).toFixed(1)+'deg');
}
function livroAtualiza(){
  capaAtualiza();
  if(reduzido){ alinha(1); reescreve(1); desenhaRede(1); return }
  const p=progresso();
  if(p===pAtual) return; pAtual=p;
  const r1=ease(clamp((p-.30)/.10))*180, r2=ease(clamp((p-.74)/.10))*180;
  l1.style.setProperty('--r',r1.toFixed(1)+'deg'); l2.style.setProperty('--r',r2.toFixed(1)+'deg');
  l1.style.setProperty('--sh',(Math.sin(r1*Math.PI/180)*.55).toFixed(2)); l2.style.setProperty('--sh',(Math.sin(r2*Math.PI/180)*.55).toFixed(2));
  l1.style.zIndex=r1>=90?1:3; l2.style.zIndex=r2>=90?4:2;
  visib(r1,r2);
  alinha(clamp((p-.08)/.20)); reescreve(clamp((p-.42)/.30)); desenhaRede(clamp((p-.84)/.15));
}
function vp(e){ const r=e.getBoundingClientRect(); return clamp((innerHeight*.9-r.top)/(Math.max(r.height,1)*.8+innerHeight*.25)) }
function linearAtualiza(){
  if(reduzido){ alinha(1); reescreve(1); desenhaRede(1); return }
  alinha(vp($('#lr-tipos'))); reescreve(vp($('.lr-f-cartoes'))); desenhaRede(vp($('#lr-mapa')));
}

/* ---------- a lâmpada: segue o cursor (desktop) ou o scroll (390) ---------- */
const lamp=$('#lr-lamp');
let PX=innerWidth*.62, PY=innerHeight*.4, cx=PX, cy=PY;
addEventListener('pointermove',e=>{ if(e.pointerType==='touch'||linear) return; PX=e.clientX; PY=e.clientY },{passive:true});
function alvoMovel(){ const h=document.documentElement.scrollHeight-innerHeight; PX=innerWidth*.5; PY=innerHeight*(.25+.5*(h>0?scrollY/h:0)) }
let folhas=[];
function luz(){
  const vh=innerHeight;
  for(const f of folhas){
    const r=f.getBoundingClientRect(); if(r.bottom<-200||r.top>vh+200) continue;
    const mx=r.left+r.width/2, my=r.top+r.height/2, dx=mx-cx, dy=my-cy, d=Math.hypot(dx,dy)||1, m=6+16*Math.max(0,1-d/1100), s=f.style;
    const ex=Math.max(r.left-cx,0,cx-r.right), ey=Math.max(r.top-cy,0,cy-r.bottom), de=Math.hypot(ex,ey);
    s.setProperty('--lx',(cx-r.left).toFixed(0)+'px'); s.setProperty('--ly',(cy-r.top).toFixed(0)+'px');
    s.setProperty('--li',Math.pow(Math.max(0,1-de/700),.9).toFixed(2));
    s.setProperty('--sx',(Math.round(dx/d*m/2)*2)+'px'); s.setProperty('--sy',(Math.round((dy/d*m*.6+8)/2)*2)+'px');
  }
  lamp.style.transform=`translate3d(${cx.toFixed(0)}px,${cy.toFixed(0)}px,0)`;
  if(!linear){ const b=livro.getBoundingClientRect(); livro.style.setProperty('--mx',(cx-b.left+20).toFixed(0)+'px'); livro.style.setProperty('--my',(cy-b.top+20).toFixed(0)+'px') }
  /* nós da rede acendem por proximidade da luz */
  if((!reduzido&&pAtual>.8)||linear){
    const sv=svg.getBoundingClientRect(); if(sv.width>0&&sv.bottom>0&&sv.top<vh){ const k=sv.width/520;
      nos.forEach(n=>{ const X=sv.left+n.x*k, Y=sv.top+n.y*k; n.el.classList.toggle('lr-on',Math.hypot(X-cx,Y-cy)<150) }) }
  }
}

/* ---------- a oficina: conferir a regra ---------- */
const FALTA={ins:$('#lr-c-ins'),obj:$('#lr-c-obj'),efe:$('#lr-c-efe')};
function confere(){
  const ins=$('#lr-f-ins').value.trim(), efe=$('#lr-f-efe').value.trim(), res=$('#lr-f-res').value, reg=$('#lr-f-reg').checked, m=[], f={ins:0,obj:0,efe:0};
  if(!ins){m.push('Falta escrever a instrução.');f.ins=1}
  if(!efe){m.push('Falta o efeito esperado: sem ele, não há como saber se a ordem serviu.');f.obj=1}
  if(ins&&efe&&ins.toLowerCase()===efe.toLowerCase()){m.push('A instrução e o efeito são iguais: confira se você descreveu o objetivo, não só a ordem.');f.obj=1}
  if(res==='Ainda não definido'){m.push('Sem responsável definido, ninguém responde pelo desvio.');f.efe=1}
  if(!reg){m.push('Sem registro, não dá para contestar depois.');f.efe=1}
  $('#lr-registro').textContent=m.length?m.join(' '):'A regra tem instrução, efeito, responsável e registro. Ainda assim, teste com um caso real antes de confiar.';
  Object.keys(FALTA).forEach(k=>FALTA[k].classList.toggle('lr-falta',!!f[k]));
}
$('#lr-checar').addEventListener('click',confere);
$('#lr-limpar').addEventListener('click',()=>{ $('#lr-f-ins').value='';$('#lr-f-efe').value='';$('#lr-f-res').selectedIndex=0;$('#lr-f-reg').checked=true;$('#lr-registro').textContent='';Object.values(FALTA).forEach(e=>e.classList.remove('lr-falta')) });

/* ---------- loop, pausa, visibilidade ---------- */
let raf=0, ag=false;
function frame(){
  raf=0; if(pausado||document.hidden) return;
  if(linear) alvoMovel();
  cx+=(PX-cx)*.12; cy+=(PY-cy)*.12;
  if(!linear) livroAtualiza(); else linearAtualiza();
  luz();
  raf=requestAnimationFrame(frame);
}
function visibTodos(){ Object.values(faces).forEach(e=>e.classList.remove('lr-off')) }
function tudo(){ modo(); folhas=$$('.lr-folha'); if(linear){alvoMovel();cx=PX;cy=PY;linearAtualiza();visibTodos()}else{pAtual=-1;livroAtualiza()} luz() }
function liga(){ if(!raf&&!pausado&&!document.hidden) raf=requestAnimationFrame(frame) }
addEventListener('scroll',()=>{ if(ag) return; ag=true; requestAnimationFrame(()=>{ag=false; if(pausado){ if(linear){alvoMovel();linearAtualiza()}else livroAtualiza(); luz() }}) },{passive:true});
document.addEventListener('visibilitychange',()=>{ if(document.hidden){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
const bt=$('#lr-pausa');
function rotulo(){bt.textContent=reduzido?'movimento pausado':(pausado?'retomar movimento':'pausar movimento');bt.setAttribute('aria-pressed',String(pausado));root.classList.toggle('lr-pausado',pausado)}
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
rotulo();
addEventListener('resize',tudo);
addEventListener('load',tudo);
tudo();
if(reduzido){ alinha(1); reescreve(1); desenhaRede(1); visibTodos(); cx=innerWidth*.6; cy=innerHeight*.35; luz() } else liga();
});
