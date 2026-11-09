import { registar } from "../motor.js";

// Atmosfera «O placar» (STAR-48, protótipo STAR-51/08): a única página clara da série.
// O hero escuro «sobe» ao papel (--sol); um gráfico de dispersão em SVG (proximidade × preocupação)
// recebe as obras por década ao rolar; filtros, destaques por fase, ficha e tabela equivalente.
// Os dados vêm do servidor pelo json_script #pl-dados (sem pedir ficheiros). A única chamada de
// rede é o POST do voto do leitor, para o endereço que o próprio servidor indica em voto_url.
// Com movimento reduzido (ou «pausar movimento»): 30 pontos, todos os destaques e a tabela visível.
registar("atmosfera:placar", ({ el, reduzido }) => {
const root=el.closest('.pl-raiz');
const $=(s,r=root)=>r.querySelector(s), $$=(s,r=root)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const movel=()=>innerWidth<900;
const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let pausado=reduzido;
if(reduzido) root.classList.add('pl-estatico');
const anima=()=>!pausado&&!reduzido&&!movel();

/* ---------- os dados: obras, médias dos leitores e voto do próprio leitor ---------- */
const DADOS=JSON.parse($('#pl-dados').textContent);
const D=DADOS.obras;
const N=D.length;
const medias=DADOS.medias||{};   /* id -> {proximidade, preocupacao, n}, só obras com n ≥ 1 */
const meus=DADOS.meus||{};       /* id -> [perto, preocupação], só do leitor com sessão */
const GR={filme:{c:'#0072B2',f:'c'},tv:{c:'#C2410C',f:'s'},jogo:{c:'#7B3FA0',f:'t'},pag:{c:'#2E7D32',f:'d'}};
D.forEach((o,i)=>{o.i=i;o.g=o.grupo});
const FASES={1:['her-2013','be-right-back-2013'],2:['ghost-shell-1989','matrix-1999'],3:['person-interest-2011','minority-report-2002']};
const idx=id=>D.findIndex(o=>o.id===id);

/* ---------- o gráfico: geometria ---------- */
const X0=70,X1=680,Y0=44,Y1=500, SX=(X1-X0)/5, SY=(Y1-Y0)/5;
const px=x=>X0+x*SX, py=y=>Y1-y*SY;
/* pontos de mesma nota formam um anel e o anel inteiro fica dentro da área (nos bordos, desloca-se para dentro) */
function anel(n){
  if(n===1) return {off:[[0,0]],R:0};
  const off=[]; const r1=n<=6?Math.max(13,10.5*n/Math.PI):22;
  const n1=n<=6?n:6; for(let k=0;k<n1;k++){const a=-Math.PI/2+k*2*Math.PI/n1; off.push([r1*Math.cos(a),r1*Math.sin(a)])}
  let R=r1;
  if(n>6){ const n2=n-6, r2=42; for(let k=0;k<n2;k++){const a=-Math.PI/2+(k+.5)*2*Math.PI/n2; off.push([r2*Math.cos(a),r2*Math.sin(a)])} R=r2 }
  return {off,R};
}
const POS=[];
(function(){
  const grupos={}; D.forEach(o=>{const k=o.proximidade+','+o.preocupacao; (grupos[k]=grupos[k]||[]).push(o)});
  Object.values(grupos).forEach(g=>{
    const {off,R}=anel(g.length), m=R+11;
    const cx=clamp(px(g[0].proximidade),X0+m,X1-m), cy=clamp(py(g[0].preocupacao),Y0+m,Y1-m);
    g.forEach((o,k)=>{POS[o.i]={x:cx+off[k][0],y:cy+off[k][1]}});
  });
})();
const forma=(f,r,c)=>f==='c'?`<circle class="pl-forma" r="${r}" fill="${c}"/>`:f==='s'?`<rect class="pl-forma" x="${-r}" y="${-r}" width="${2*r}" height="${2*r}" fill="${c}"/>`:f==='t'?`<path class="pl-forma" d="M0 ${-r*1.15}L${r*1.05} ${r*.85}L${-r*1.05} ${r*.85}Z" fill="${c}"/>`:`<path class="pl-forma" d="M0 ${-r*1.2}L${r*1.2} 0L0 ${r*1.2}L${-r*1.2} 0Z" fill="${c}"/>`;

(function desenha(){
  let h=`<rect class="pl-perto" x="${px(2.5)}" y="${Y0}" width="${X1-px(2.5)}" height="${Y1-Y0}"/>`;
  for(let i=0;i<=5;i++){ h+=`<line class="pl-gr" x1="${px(i)}" y1="${Y0}" x2="${px(i)}" y2="${Y1}"/><line class="pl-gr" x1="${X0}" y1="${py(i)}" x2="${X1}" y2="${py(i)}"/>`;
    h+=`<text x="${px(i)}" y="${Y1+20}" text-anchor="middle">${i}</text><text x="${X0-12}" y="${py(i)+4}" text-anchor="end">${i}</text>` }
  h+=`<line class="pl-md" x1="${px(2.5)}" y1="${Y0}" x2="${px(2.5)}" y2="${Y1}"/><line class="pl-md" x1="${X0}" y1="${py(2.5)}" x2="${X1}" y2="${py(2.5)}"/><rect class="pl-moldura" x="${X0}" y="${Y0}" width="${X1-X0}" height="${Y1-Y0}"/>`;
  /* os rótulos dos quadrantes ficam FORA da área, acima e abaixo da moldura */
  h+=`<text class="pl-quadr" x="${X0}" y="${Y0-12}">Distante · pede cuidado</text><text class="pl-quadr" x="${X1}" y="${Y0-12}" text-anchor="end">Próximo · pede cuidado</text>`;
  h+=`<text class="pl-quadr" x="${X0}" y="${Y1+44}">Distante · menos grave</text><text class="pl-quadr" x="${X1}" y="${Y1+44}" text-anchor="end">Próximo · menos grave</text>`;
  h+=`<text class="pl-tit" x="${(X0+X1)/2}" y="${Y1+68}" text-anchor="middle">Perto: 0 = fantasia · 5 = já é cotidiano</text>`;
  h+=`<text class="pl-tit" transform="translate(16 ${(Y0+Y1)/2}) rotate(-90)" text-anchor="middle">Preocupação: 0 = quase nenhuma · 5 = risco catastrófico</text>`;
  h+=`<g id="pl-leitores" class="pl-leitor-g" hidden></g><g id="pl-aros"></g>`;
  D.forEach(o=>{ const p=POS[o.i], G=GR[o.g];
    h+=`<g class="pl-pt" data-i="${o.i}" tabindex="0" role="button" aria-label="${esc(o.titulo)}, ${o.ano}, ${esc(o.midia)}. Perto ${o.proximidade}, preocupação ${o.preocupacao}. Abrir a ficha." transform="translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})"><circle r="14" fill="transparent"/>${forma(G.f,8,G.c)}</g>`; });
  h+=`<g id="pl-rots"></g>`;
  $('#pl-plot').innerHTML=h;
})();
const pts=$$('#pl-plot .pl-pt');

/* ---------- visibilidade: década de entrada, filtros ---------- */
let corte=2100, midias=new Set(['filme','tv','jogo','pag']), dec='';
const decOk=o=>!dec||(dec==='a'?o.ano<=1979:dec==='b'?o.ano>=1980&&o.ano<=1999:o.ano>=2000);
const passa=o=>midias.has(o.g)&&decOk(o);
function aplica(){
  let n=0; pts.forEach((p,i)=>{ const o=D[i], ve=o.ano<=corte; if(ve) n++; p.classList.toggle('pl-oculto',!ve); p.classList.toggle('pl-fraco',ve&&!passa(o)); p.setAttribute('tabindex',ve&&passa(o)?'0':'-1') });
  $('#pl-cont').textContent=corte>=2100?`${N} de ${N} · todos os anos`:`${n} de ${N} · ano ${Math.round(corte)}`;
  if(!sec.hidden) tabela();
}

/* ---------- destaques por fase ---------- */
let fase=0, fixa=0;
function larg(t){return t.length*6.9+4}
function destaca(ids){
  const aros=$('#pl-aros'), rots=$('#pl-rots'); aros.innerHTML=''; rots.innerHTML='';
  const marc=D.map((o,i)=>({x:POS[i].x-10,y:POS[i].y-10,w:20,h:20}));
  const ocup=[]; const cruza=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
  ids.forEach(id=>{ const i=idx(id); if(i<0||!D[i].ano||D[i].ano>corte) return; const p=POS[i], t=D[i].titulo, w=larg(t), h=15;
    aros.insertAdjacentHTML('beforeend',`<circle class="pl-aro" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="16"/>`);
    const c=[{x:p.x+20,y:p.y-11,a:'start',bx:p.x+20,by:p.y+4},{x:p.x-20-w,y:p.y-11,a:'end',bx:p.x-20,by:p.y+4},{x:p.x-w/2,y:p.y-34,a:'middle',bx:p.x,by:p.y-22},{x:p.x-w/2,y:p.y+20,a:'middle',bx:p.x,by:p.y+33}];
    const dentro=r=>r.x>=X0+3&&r.x+w<=X1-3&&r.y>=Y0+3&&r.y+h<=Y1-3;
    let sel=c.find(r=>{const R={x:r.x,y:r.y,w,h}; return dentro(r)&&!marc.some((m,k)=>k!==i&&cruza(R,m))&&!ocup.some(o=>cruza(R,o))})||c.find(r=>dentro(r))||c[2];
    ocup.push({x:sel.x,y:sel.y,w,h});
    rots.insertAdjacentHTML('beforeend',`<text class="pl-rot" x="${sel.bx.toFixed(1)}" y="${sel.by.toFixed(1)}" text-anchor="${sel.a}">${esc(t)}</text>`);
  });
}
const NOMES={0:'nenhum',1:'se aproximaram',2:'sem demonstração',3:'pedem atenção',9:'todos'};
function mostraFase(f){
  const ids=f===9?[].concat(FASES[1],FASES[2],FASES[3]):(FASES[f]||[]);
  destaca(ids); $('#pl-dest').textContent='Destaque: '+(f===9?'todos os três grupos':f?NOMES[f]+' ('+ids.map(id=>D[idx(id)].titulo).join('; ')+')':'nenhum');
}
$$('[data-f]').forEach(b=>b.addEventListener('click',()=>{ const f=+b.dataset.f; fixa=fixa===f?0:f; $$('[data-f]').forEach(x=>x.setAttribute('aria-pressed',String(+x.dataset.f===fixa))); mostraFase(fixa||fase) }));

/* ---------- filtros ---------- */
$$('[data-m]').forEach(b=>b.addEventListener('click',()=>{ const m=b.dataset.m, on=!midias.has(m); on?midias.add(m):midias.delete(m); b.setAttribute('aria-pressed',String(on)); aplica() }));
$('#pl-f-dec').addEventListener('change',e=>{ dec=e.target.value; aplica() });

/* ---------- a ficha (dentro do gráfico, acima do ponto ou longe do canto) ---------- */
const ficha=$('#pl-ficha'), pw=$('#pl-pw'); let aberto=-1;
const f1=n=>n.toFixed(1).replace('.',',');
function posFicha(i){
  if(movel()){ ficha.style.left=ficha.style.top=''; return }
  const sv=$('#pl-plot'), k=sv.getBoundingClientRect().width/700, p=POS[i], W=pw.clientWidth;
  const fw=ficha.offsetWidth, fh=ficha.offsetHeight, topP=Y0*k+4, botP=Y1*k-4;
  let l=clamp(p.x*k-fw/2,X0*k+4,Math.min(W-fw-4,X1*k-fw-4)), t=p.y*k-fh-16;
  if(t<topP) t=p.y*k+16;
  t=clamp(t,topP,Math.max(topP,botP-fh));
  ficha.style.left=l.toFixed(0)+'px'; ficha.style.top=(t+sv.offsetTop).toFixed(0)+'px';
}
function abre(i){
  const o=D[i], m=medias[o.id]; aberto=i; pts.forEach((p,k)=>p.classList.toggle('pl-sel',k===i));
  $('#pl-fi-t').textContent=o.titulo; $('#pl-fi-m').textContent=o.ano+' · '+o.midia; $('#pl-fi-n').textContent='Perto: '+o.proximidade+' · Preocupação: '+o.preocupacao; $('#pl-fi-j').textContent=o.justificativa;
  $('#pl-fi-l').textContent=m?`Leitores: perto ${f1(m.proximidade)}, preocupação ${f1(m.preocupacao)} (${m.n} ${m.n===1?'voto':'votos'}).`:'Leitores: ainda sem votos nesta obra.';
  ficha.hidden=false; posFicha(i);
}
function fecha(){ aberto=-1; ficha.hidden=true; pts.forEach(p=>p.classList.remove('pl-sel')) }
pts.forEach((p,i)=>{
  p.addEventListener('click',e=>{e.stopPropagation(); aberto===i?fecha():abre(i)});
  p.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){e.preventDefault(); aberto===i?fecha():abre(i)} else if(e.key==='Escape') fecha() });
  p.addEventListener('mouseenter',()=>{ if(!movel()&&!ficha.matches(':hover')) abre(i) });
});
$('#pl-plot').addEventListener('mouseleave',()=>{ if(!movel()&&document.activeElement.closest&&!document.activeElement.closest('.pl-pt')) fecha() });
$('#pl-f-fechar').addEventListener('click',fecha);
/* só dentro da raiz: não sequestra o Escape nem os cliques do cabeçalho do site */
root.addEventListener('keydown',e=>{ if(e.key==='Escape') fecha() });
root.addEventListener('click',e=>{ if(!e.target.closest('#pl-pw')) fecha() });

/* ---------- tabela equivalente: as linhas vêm do servidor; aqui só se filtram e ordenam ---------- */
const sec=$('#pl-tab-sec'), bt2=$('#pl-b-tab'), corpo=$('#pl-tab tbody');
const LINHAS=new Map($$('tr[data-id]',corpo).map(tr=>[tr.dataset.id,tr]));
let ord={k:'ano',d:1};
function tabela(){
  const vis=D.filter(o=>o.ano<=corte&&passa(o)).sort((a,b)=>{const A=a[ord.k],B=b[ord.k]; return (typeof A==='string'?A.localeCompare(B,'pt'):A-B)*ord.d||a.ano-b.ano});
  const ids=new Set(vis.map(o=>o.id));
  LINHAS.forEach((tr,id)=>{ tr.hidden=!ids.has(id) });
  vis.forEach(o=>corpo.appendChild(LINHAS.get(o.id)));
  $$('#pl-tab thead th').forEach(th=>{const b=th.querySelector('button'); if(b) th.setAttribute('aria-sort',b.dataset.k===ord.k?(ord.d>0?'ascending':'descending'):'none')});
}
$$('#pl-tab thead button').forEach(b=>b.addEventListener('click',()=>{ ord=ord.k===b.dataset.k?{k:ord.k,d:-ord.d}:{k:b.dataset.k,d:1}; tabela() }));
function tabVis(v){ sec.hidden=!v; bt2.setAttribute('aria-pressed',String(v)); bt2.textContent=v?'Ocultar a tabela':'Ver como tabela'; if(v) tabela() }
bt2.addEventListener('click',()=>{ tabVis(sec.hidden) });
tabVis(reduzido); /* a tabela começa escondida; no modo reduzido fica visível e legível */

/* ---------- a camada dos leitores: médias REAIS dos votos (nada simulado) ---------- */
function camada(){
  const g=$('#pl-leitores'); let h='';
  Object.keys(medias).forEach(id=>{ const k=idx(id); if(k<0) return; const m=medias[id], p=POS[k], x=clamp(px(m.proximidade),X0+14,X1-14), y=clamp(py(m.preocupacao),Y0+14,Y1-14);
    h+=`<line class="pl-leitor-lig" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/><circle class="pl-leitor" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="13"><title>Média dos leitores em ${esc(D[k].titulo)}: perto ${f1(m.proximidade)}, preocupação ${f1(m.preocupacao)} (${m.n} ${m.n===1?'voto':'votos'})</title></circle>` });
  g.innerHTML=h; g.hidden=!$('#pl-f-camada').checked;
}
$('#pl-f-camada').addEventListener('change',camada);
function avisoVotos(){
  const n=Object.values(medias).reduce((s,m)=>s+m.n,0);
  $('#pl-aviso').textContent=`Média real dos votos de leitores com conta: ${n} ${n===1?'voto':'votos'} até agora. A amostra é pequena e se escolheu sozinha. Isto não é pesquisa científica. Cada pessoa conta uma vez por obra; só guardamos as notas, sem texto livre.`;
}

/* ---------- o voto: único pedido ao servidor (POST com o token CSRF do cookie) ---------- */
const form=$('#pl-voto');
const csrf=()=>{ const c=document.cookie.split('; ').find(x=>x.startsWith('csrftoken=')); return c?decodeURIComponent(c.slice(10)):'' };
if(form){
  const sel=$('#pl-f-obra'), fx=$('#pl-f-x'), fy=$('#pl-f-y'), reg=$('#pl-registro'), btn=$('#pl-enviar');
  const mostra=()=>{ $('#pl-o-x').textContent=fx.value; $('#pl-o-y').textContent=fy.value };
  const carrega=()=>{ const v=meus[sel.value]; if(v){ fx.value=v[0]; fy.value=v[1] } mostra() };
  fx.addEventListener('input',mostra); fy.addEventListener('input',mostra); sel.addEventListener('change',carrega);
  carrega();
  const ERROS={401:'Entre na sua conta para votar.',429:'Você atingiu o limite de votos de hoje. Volte amanhã.',400:'Não foi possível registrar: confira a obra e as notas.'};
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const id=sel.value, x=+fx.value, y=+fy.value, i=idx(id);
    btn.disabled=true; reg.textContent='Enviando o seu voto…';
    try{
      const r=await fetch(DADOS.voto_url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify({obra:id,proximidade:x,preocupacao:y})});
      if(!r.ok){ reg.textContent=ERROS[r.status]||'Não foi possível registrar agora. Tente de novo mais tarde.'; return }
      const m=await r.json();
      medias[id]={proximidade:m.proximidade,preocupacao:m.preocupacao,n:m.n}; meus[id]=[x,y];
      $('#pl-f-camada').checked=true; camada(); avisoVotos();
      reg.textContent=`Seu voto em «${D[i].titulo}»: perto ${x}, preocupação ${y}. Média dos leitores (${m.n} ${m.n===1?'voto':'votos'}, amostra pequena, não é pesquisa científica): perto ${f1(m.proximidade)}, preocupação ${f1(m.preocupacao)}. Nota editorial: perto ${D[i].proximidade}, preocupação ${D[i].preocupacao}.`;
    }catch(err){ reg.textContent='Sem conexão: o voto não foi registrado.' }
    finally{ btn.disabled=false }
  });
}
camada();

/* ---------- da noite ao papel e entrada por década ---------- */
const hero=$('#pl-hero'), topo=$('#pl-topo'), b1=$('#pl-b1'), b2=$('#pl-b2');
const relRaiz=()=>-root.getBoundingClientRect().top; /* rolagem relativa à raiz (o cabeçalho do site fica por cima) */
let faseAuto=-1;
function atualiza0(){
  const vh=innerHeight, s=relRaiz();
  hero.style.setProperty('--sol',reduzido?1:clamp(s/(vh*.9)).toFixed(3));
  topo.classList.toggle('pl-claro',s>hero.offsetHeight+vh*.15);
}
function atualiza(){
  const vh=innerHeight;
  atualiza0();
  if(anima()){
    const r=b1.getBoundingClientRect(), p=clamp((vh*.8-r.top)/(r.height*.9));
    const c=r.top>vh*.8?1919:(p>=.999||r.bottom<0?2100:1920+p*(2023-1920)); corte=Math.round(c);
    aplica();
    const r2=b2.getBoundingClientRect(); let f=0;
    if(r2.top<vh*.7&&r2.bottom>vh*.3){ const q=clamp((vh*.7-r2.top)/(r2.height*.9)); f=q<.34?1:q<.67?2:3 }
    if(f!==faseAuto){ faseAuto=f; fase=f; if(!fixa) mostraFase(f) }
  }
}
function estatico(){ corte=2100; aplica(); fase=9; if(!fixa) mostraFase(9) }

/* ---------- pausa e visibilidade (não há loop contínuo: só o scroll, por rAF) ---------- */
let ag=false, ultimo=null;
function tick(){ ag=false; if(!anima()||document.hidden) return; const s=relRaiz(); if(s!==ultimo){ultimo=s; atualiza()} }
addEventListener('scroll',()=>{ atualiza0(); if(ag) return; ag=true; requestAnimationFrame(tick) },{passive:true});
const bt=$('#pl-pausa');
function rotulo(){bt.textContent=reduzido?'movimento pausado (modo reduzido)':(pausado?'retomar movimento':'pausar movimento');bt.setAttribute('aria-pressed',String(pausado));root.classList.toggle('pl-pausado',pausado)}
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado) estatico(); else {faseAuto=-1; atualiza()} });
rotulo();
function modo(){ if(!anima()) estatico(); else {faseAuto=-1; atualiza()} }
addEventListener('resize',()=>{ modo(); if(aberto>=0) posFicha(aberto) });
modo(); atualiza0();
addEventListener('load',()=>{ modo(); atualiza0() });
});
