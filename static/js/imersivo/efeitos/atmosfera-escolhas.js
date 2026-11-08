import { registar } from "../motor.js";

// Atmosfera «Escolhas da máquina» (STAR-46, protótipo STAR-51/06): narrativa ramificada com estado no cliente.
// Duas escolhas, quatro finais, todos abríveis; o caminho só é guardado no navegador com consentimento (sem rede).
// Só teclado funciona (botões nativos). Com movimento reduzido: versão linear, os ramos e os finais ficam legíveis e estáticos.
registar("atmosfera:escolhas", ({ el, reduzido }) => {
const root=el.closest('.em-raiz');
const $=(s,r=root)=>r.querySelector(s), $$=(s,r=root)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const movel=()=>innerWidth<900;
let pausado=reduzido, pedido=null; /* pedido: o leitor força interativo (true) ou linear (false) */
if(reduzido) root.classList.add('em-estatico');

/* ---------- modo linear/interativo ---------- */
function modo(){
  const lin=pedido===null?(reduzido||movel()):!pedido;
  root.classList.toggle('em-linear',lin);
  const b=$('#em-modo'); b.textContent=lin?'Ver versão interativa':'Ver versão linear'; b.setAttribute('aria-pressed',String(!lin));
  $$('.em-final-item>button').forEach(x=>{ x.tabIndex=lin?-1:0; if(lin) x.setAttribute('aria-expanded','true') });
}
$('#em-modo').addEventListener('click',()=>{ pedido=root.classList.contains('em-linear'); modo(); render() });

/* ---------- o estado: {a,b,seen}; só vai para o localStorage com consentimento ---------- */
const CH='star46.p6', FIN={A1:'A1 · Aceitar o resultado',A2:'A2 · Pedir o registro depois',B1:'B1 · Mudar a meta',B2:'B2 · Manter a meta, com um aviso'};
let S={a:null,b:null,seen:[]};
try{ const j=localStorage.getItem(CH); if(j){ const o=JSON.parse(j); if(o&&typeof o==='object'){ S={a:o.a==='A'||o.a==='B'?o.a:null,b:FIN[o.b]?o.b:null,seen:Array.isArray(o.seen)?o.seen.filter(x=>FIN[x]):[]}; $('#em-f-cons').checked=true } } }catch(e){}
function guarda(){ try{ if($('#em-f-cons').checked) localStorage.setItem(CH,JSON.stringify(S)); else localStorage.removeItem(CH) }catch(e){} }
function vistos(f){ if(!S.seen.includes(f)) S.seen.push(f) }

function render(){
  const rc=S.a==='A'?'111,227,193':S.a==='B'?'242,179,94':'154,164,255';
  root.style.setProperty('--rc',rc);
  const ar=$('#em-arvore1'); ar.classList.toggle('em-esc-A',S.a==='A'); ar.classList.toggle('em-esc-B',S.a==='B');
  $$('[data-a]').forEach(b=>b.setAttribute('aria-pressed',String(S.a===b.dataset.a)));
  $('#em-cA').hidden=S.a!=='A'; $('#em-cB').hidden=S.a!=='B';
  /* nó 2: depende do 1 */
  const e2=$('#em-esc2'), v=$('#em-vazio2'); e2.innerHTML='';
  v.hidden=!!S.a; e2.hidden=!S.a;
  if(S.a){ [S.a+'1',S.a+'2'].forEach(f=>{ const b=document.createElement('button'); b.type='button'; b.className='em-no-btn em-'+S.a; b.dataset.b=f; b.textContent=FIN[f]; b.setAttribute('aria-pressed',String(S.b===f)); e2.appendChild(b) }) }
  const c2=$('#em-conseq2'); c2.hidden=!S.b; c2.className='em-conseq em-'+(S.a||'');
  if(S.b) c2.textContent='Final '+FIN[S.b]+' — '+$('.em-final-item[data-f="'+S.b+'"] .em-tx').textContent;
  /* finais */
  const lin=root.classList.contains('em-linear');
  $$('.em-final-item').forEach(li=>{ const f=li.dataset.f, vi=S.seen.includes(f); li.classList.toggle('em-visto',vi); $('.em-sel',li).textContent=vi?'visto':'por ver'; $('button',li).setAttribute('aria-expanded',String(lin||li.classList.contains('em-aberto'))) });
  $('#em-contador').textContent=S.seen.length+' de 4 finais vistos';
  $$('#em-arv4 .em-n[id]').forEach(n=>n.classList.toggle('em-visto',S.seen.includes(n.id.slice(5))));
  ['A','B'].forEach(k=>$('#em-e'+k).classList.toggle('em-on-'+k.toLowerCase(),S.a===k));
  ['A1','A2','B1','B2'].forEach(f=>$('#em-e'+f).classList.toggle('em-on-'+f[0].toLowerCase(),S.seen.includes(f)));
}
$('#em-p-esc1').addEventListener('click',e=>{ const b=e.target.closest('[data-a]'); if(!b) return; if(S.a!==b.dataset.a){S.a=b.dataset.a;S.b=null} guarda(); render() });
$('#em-esc2').addEventListener('click',e=>{ const b=e.target.closest('[data-b]'); if(!b) return; S.b=b.dataset.b; vistos(S.b); guarda(); render(); const n=$('#em-esc2 [data-b="'+S.b+'"]'); n&&n.focus() });
$('#em-abrir').addEventListener('click',()=>{ const f=$('#em-f-final').value; if(!f){ $('#em-registro').textContent='Escolha primeiro um final na lista.'; return } vistos(f); $('.em-final-item[data-f="'+f+'"]').classList.add('em-aberto'); guarda(); render(); $('#em-registro').textContent='Final '+FIN[f]+' aberto no ato 4. '+S.seen.length+' de 4 vistos.' });
$$('.em-final-item>button').forEach(b=>b.addEventListener('click',()=>{ const li=b.parentElement; const abre=!li.classList.contains('em-aberto'); li.classList.toggle('em-aberto',abre); if(abre) vistos(li.dataset.f); guarda(); render() }));
$('#em-f-cons').addEventListener('change',()=>{ guarda(); $('#em-registro').textContent=$('#em-f-cons').checked?'Caminho guardado neste aparelho. Você pode limpar quando quiser.':'Nada fica guardado: o caminho vale só para esta visita.' });
$('#em-limpar').addEventListener('click',()=>{ S={a:null,b:null,seen:[]}; $$('.em-final-item').forEach(l=>l.classList.remove('em-aberto')); $('#em-f-final').selectedIndex=0; try{localStorage.removeItem(CH)}catch(e){} $('#em-f-cons').checked=false; render(); $('#em-registro').textContent='Caminho apagado deste aparelho.' });

/* ---------- trilhas de dados: a velocidade segue o scroll ---------- */
const tr=[$('#em-t0'),$('#em-t1'),$('#em-t2')].map(p=>({p,L:p.getTotalLength?p.getTotalLength():300}));
const pts=[{el:$('#em-p0'),t:0,i:0,d:1},{el:$('#em-p1'),t:.5,i:1,d:1},{el:$('#em-p2'),t:0,i:0,d:-1},{el:$('#em-p3'),t:.55,i:2,d:-1}];
const pontoEm=x=>{ const tt=tr[x.i]; const q=x.d>0?x.t:1-x.t; let pt; try{pt=tt.p.getPointAtLength(q*tt.L)}catch(e){return} x.el.setAttribute('cx',pt.x.toFixed(1)); x.el.setAttribute('cy',pt.y.toFixed(1)) };
let sPrev=scrollY, vel=0;
function trilhas(){
  const dv=Math.abs(scrollY-sPrev); sPrev=scrollY; vel+=(Math.min(dv,60)-vel)*.2;
  const v=.0025+vel*.00045;
  pts.forEach(x=>{ x.t+=v; if(x.t>1){x.t=0;x.i=x.d>0?(x.i===0?1:0):(x.i===0?2:0)} pontoEm(x) });
}

/* ---------- caminhos do herói e névoa ---------- */
const ca=$('#em-ca'), cb=$('#em-cb'), ns=[$('#em-n1'),$('#em-n2')], KN=[.04,.12];
let PXn=.5;
addEventListener('pointermove',e=>{ if(e.pointerType==='touch'||movel()) return; PXn=e.clientX/innerWidth },{passive:true});
function paralaxe(){
  ca.style.setProperty('--d',(1-clamp(.35+scrollY/innerHeight*.9)).toFixed(3)); cb.style.setProperty('--d',(1-clamp(.35+scrollY/innerHeight*.7)).toFixed(3));
  ns.forEach((n,i)=>n.style.transform=`translate3d(${Math.round((PXn-.5)*-30*(i+1))}px,${Math.round(-scrollY*KN[i])}px,0)`);
}

/* ---------- loop, pausa, visibilidade ---------- */
let raf=0,ag=false;
function frame(){
  raf=0; if(pausado||document.hidden) return;
  paralaxe(); trilhas();
  raf=requestAnimationFrame(frame);
}
function liga(){ if(!raf&&!pausado&&!document.hidden) raf=requestAnimationFrame(frame) }
addEventListener('scroll',()=>{ if(ag||reduzido) return; ag=true; requestAnimationFrame(()=>{ag=false; if(pausado) paralaxe()}) },{passive:true});
document.addEventListener('visibilitychange',()=>{ if(document.hidden){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
const bt=$('#em-pausa');
function rotulo(){bt.textContent=reduzido?'movimento pausado (modo reduzido)':(pausado?'retomar movimento':'pausar movimento');bt.setAttribute('aria-pressed',String(pausado));root.classList.toggle('em-pausado',pausado)}
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado){if(raf){cancelAnimationFrame(raf);raf=0}} else liga() });
rotulo();
addEventListener('resize',()=>{ modo(); render() });
modo(); render(); pts.forEach(pontoEm);
if(reduzido){ ca.style.setProperty('--d','0'); cb.style.setProperty('--d','0') } else liga();
});
