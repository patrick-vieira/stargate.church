import { registar } from "../motor.js";

// Atmosfera «O que é ser humano?» (STAR-43, protótipo aprovado no STAR-51): sala de vidro com painéis em
// parallax, reflexo que segue o cursor e o teste de três perguntas que reordena o ato 2 e escolhe o final.
// Sem biblioteca: CSS + JS próprio. Com movimento reduzido a ordem fica fixa e os três finais ficam visíveis.
registar("atmosfera:ser-humano", ({ el, reduzido }) => {
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const root=el.closest('.sh-raiz');
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
let pausado=reduzido;
if(reduzido) root.classList.add('sh-estatico');

/* ---------- o teste: três perguntas, maioria, empate/nenhuma = «não sei» ---------- */
const TONS=['confiar','nao_sei','duvidar'];
const NOME={confiar:'confiar',duvidar:'duvidar',nao_sei:'não sei'};
const FINAIS={confiar:['confiar','Sua confiança mostra como uma interface produz vínculo.'],duvidar:['duvidar','Sua dúvida protege contra inferências apressadas.'],nao_sei:['não sei','A incerteza é uma resposta honesta.']};
const ORDENS={confiar:['a','b','c'],duvidar:['b','c','a'],nao_sei:['c','a','b']};
const OBS={confiar:['alinhado: você deixou a fluência pesar a favor','o observador e o observado ficam lado a lado'],duvidar:['afastado: você pede evidência antes de aproximar','os dois círculos se afastam'],nao_sei:['sobreposto: o que se vê ainda não separa os dois','os círculos se sobrepõem, tracejados']};
function respostas(){return ['sh-q1','sh-q2','sh-q3'].map(n=>{const c=$(`input[name=${n}]:checked`,root);return c?+c.value:null})}
function tom(){
  const r=respostas().filter(v=>v!==null); if(!r.length) return null;
  const c=[0,0,0]; r.forEach(v=>c[v]++); const m=Math.max(...c), idx=c.map((v,i)=>v===m?i:-1).filter(i=>i>=0);
  return idx.length===1?TONS[idx[0]]:'nao_sei';
}
const reord=$('#sh-reord'); let tomAnt='__';
function flip(ordem){
  const els=$$('.sh-vidro',reord), ant=new Map(els.map(e=>[e,e.getBoundingClientRect().top]));
  ordem.forEach((k,i)=>{const e=els.find(x=>x.dataset.k===k); e.style.order=i});
  if(reduzido||pausado) return;
  els.forEach(e=>{const dy=ant.get(e)-e.getBoundingClientRect().top; if(!dy) return; e.style.transition='none'; e.style.transform=`translateY(${dy}px)`; e.getBoundingClientRect(); e.style.transition='transform .4s ease'; e.style.transform=''});
}
function atualiza(){
  const t=tom(), n=respostas().filter(v=>v!==null).length, ef=t||'nao_sei';
  $$('#sh-prog i').forEach((i,k)=>i.classList.toggle('sh-on',k<n)); $('#sh-pt').textContent=`${n}/3 respondidas`;
  TONS.forEach(x=>root.classList.toggle('sh-tom-'+x,t===x));
  $('#sh-chip').textContent=t?`tom: ${NOME[t]}`:'tom: aguardando respostas';
  if(t!==tomAnt){tomAnt=t; flip(ORDENS[t||'confiar'])}
  $('#sh-nota-ordem').textContent=(reduzido?'Ordem fixa em «confiar»; a ordem muda no modo interativo. ':'')+'Fontes: Ex Machina, A24 · Westworld, HBO.'+(reduzido?'':' Os três parágrafos ao lado trocam de ordem conforme o tom do seu teste.');
  const o2=$('#sh-o2'), o1=$('#sh-o1'), P={null:[90,150,0],confiar:[108,132,0],duvidar:[66,186,0],nao_sei:[90,106,1]}[t]||[90,150,0];
  o1.setAttribute('cx',P[0]); o2.setAttribute('cx',P[1]); o2.setAttribute('stroke-dasharray',P[2]?'8 7':'1 0');
  $('#sh-obst').textContent=t?OBS[t][0]:'sem respostas ainda';
  $('#sh-fint').textContent=FINAIS[ef][0]; $('#sh-finp').textContent=FINAIS[ef][1]+(t?'':' (nenhuma resposta ainda: vale a regra do «não sei»)');
  $$('#sh-todos .sh-porta').forEach(p=>p.classList.toggle('sh-ativo',p.dataset.t===ef&&!!t));
}
$('#sh-teste').addEventListener('change',atualiza);
$('#sh-refazer').addEventListener('click',()=>{$$('#sh-teste input[type=radio]').forEach(i=>i.checked=false);atualiza();const f=$('input[name=sh-q1]');f&&f.focus()});
$('#sh-ver').addEventListener('click',()=>{const a=$('#sh-ato3'),h=$('#sh-t-ato3');a.scrollIntoView({behavior:reduzido||pausado?'auto':'smooth',block:'start'});h.setAttribute('tabindex','-1');setTimeout(()=>h.focus({preventScroll:true}),reduzido?0:500)});
function mostraTodos(v){const b=$('#sh-outros'),t=$('#sh-todos');t.hidden=!(v||reduzido);b.setAttribute('aria-expanded',String(!!v||reduzido));b.textContent=v?'Esconder os outros finais':'Ler os outros finais';$('#sh-chk-todos').checked=!!v;if(reduzido)b.hidden=true}
let todos=false;
$('#sh-outros').addEventListener('click',()=>{todos=!todos;mostraTodos(todos)});
$('#sh-chk-todos').addEventListener('change',e=>{todos=e.target.checked;mostraTodos(todos)});

/* ---------- a luz da sala: reflexo do cursor, brilho especular nos cartões, sombra oposta ---------- */
let vidros=[], PX=innerWidth*.62, PY=innerHeight*.38, cx=PX, cy=PY, sY=-1;
const refl=$('#sh-refl'), sala=$('#sh-sala');
const movel=()=>innerWidth<900;
addEventListener('pointermove',e=>{ if(e.pointerType==='touch'||movel()) return; PX=e.clientX; PY=e.clientY; if(pausado) luz() },{passive:true});
function luz(){
  const vw=innerWidth, vh=innerHeight, cand=[];
  for(const e of vidros){
    const r=e.getBoundingClientRect(); if(r.bottom<-160||r.top>vh+160||r.right<-160||r.left>vw+160){ if(e.__p){e.__p=false;e.classList.remove('sh-perto')} continue }
    const ex=Math.max(r.left-cx,0,cx-r.right), ey=Math.max(r.top-cy,0,cy-r.bottom), de=Math.hypot(ex,ey);
    const mx=r.left+r.width/2, my=r.top+r.height/2, dx=mx-cx, dy=my-cy, d=Math.hypot(dx,dy)||1, m=6+16*Math.max(0,1-d/1200), s=e.style;
    const qx=Math.round(dx/d*m/6)*6, qy=Math.round((dy/d*m+10)/6)*6;
    if(qx!==e.__qx||qy!==e.__qy){e.__qx=qx;e.__qy=qy;s.setProperty('--sx',qx+'px');s.setProperty('--sy',qy+'px')}
    if(de<420) cand.push({el:e,r,de});
  }
  cand.sort((a,b)=>a.de-b.de); const top=cand.slice(0,1); let lt=null;
  for(const e of vidros){ const on=top.some(c=>c.el===e); if(on!==!!e.__p){e.__p=on;e.classList.toggle('sh-perto',on)} }
  for(const c of top){
    const s=c.el.style, r=c.r;
    s.setProperty('--lx',(cx-r.left).toFixed(0)+'px'); s.setProperty('--ly',(cy-r.top).toFixed(0)+'px');
    s.setProperty('--li',Math.pow(Math.max(0,1-c.de/420),.85).toFixed(2));
    s.setProperty('--sh',(clamp((cx-r.left)/Math.max(1,r.width),-.3,1.3)*100).toFixed(0)+'%');
    if(!lt&&r.width*r.height<420000) lt=c.el;
  }
  lente(lt);
}
function lente(m){ if(lente.a===m) return; if(lente.a) lente.a.classList.remove('sh-lente'); if(m) m.classList.add('sh-lente'); lente.a=m }
function parallax(){ if(scrollY===sY) return; sY=scrollY; sala.style.setProperty('--py',(-scrollY*.16).toFixed(1)+'px') }

/* ---------- loop, pausa, visibilidade ---------- */
let raf=0,ag=false,tPrev=0,ema=16.7,lento=0;
function frame(t){
  raf=0; if(pausado||document.hidden) return;
  const dt=t-(tPrev||t); tPrev=t; if(dt>0&&dt<250){ema+=(dt-ema)*.08; if(ema>24){if(++lento>40) root.classList.add('sh-sem-blur')} else lento=Math.max(0,lento-1)}
  if(movel()){PX=innerWidth*(.5+.32*Math.sin(scrollY/300));PY=innerHeight*(.36+.08*Math.cos(scrollY/420))}
  const mover=Math.abs(PX-cx)>.3||Math.abs(PY-cy)>.3, rolou=scrollY!==sY;
  cx+=(PX-cx)*.16; cy+=(PY-cy)*.16;
  refl.style.transform=`translate3d(${cx.toFixed(1)}px,${cy.toFixed(1)}px,0)`;
  parallax(); if(mover||rolou) luz();
  raf=requestAnimationFrame(frame);
}
function liga(){ if(!raf&&!pausado&&!document.hidden) raf=requestAnimationFrame(frame) }
addEventListener('scroll',()=>{ if(ag) return; ag=true; requestAnimationFrame(()=>{ag=false; if(pausado){parallax();luz()}}) },{passive:true});
document.addEventListener('visibilitychange',()=>{ if(document.hidden){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
const bt=$('#sh-pausa');
function rotulo(){bt.textContent=reduzido?'movimento pausado':(pausado?'retomar movimento':'pausar movimento');bt.setAttribute('aria-pressed',String(pausado));root.classList.toggle('sh-pausado',pausado)}
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
rotulo();
addEventListener('resize',()=>{vidros=$$('.sh-vidro',root);luz()});
vidros=$$('.sh-vidro',root); atualiza(); mostraTodos(false); parallax();
if(reduzido){ cx=PX=innerWidth*.62; cy=PY=innerHeight*.3; luz() } else liga();
});
