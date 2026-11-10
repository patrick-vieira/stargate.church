import { registar } from "../motor.js";

// Atmosfera «Hub» (STAR-70, protótipo STAR-51/00): névoa que se abre ao cursor (shader de ruído em meia
// resolução, com alternativa 2D), luz e fundo que mudam por década, grão de filme, faixa horizontal sticky
// com 3 camadas de parallax. Sem rede e sem biblioteca. Com movimento reduzido, a 390 px e sem JS a faixa
// vira lista vertical por era. O estado (cores, classes) vive na raiz, nunca no html.
registar("atmosfera:hub", ({ el, reduzido }) => {
const root=el.closest('.hb-raiz');
const $=(s,r=root)=>r.querySelector(s), $$=(s,r=root)=>[...r.querySelectorAll(s)];
const S=root.style;
const CAB=76; /* altura do cabeçalho sticky do site */
let pausado=reduzido, faixaOn=false, e=0;
if(reduzido) root.classList.add('hb-estatico');

/* ---------- eras e cores ---------- */
const hex=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
const ERAS=[
 {nome:'Papel',anos:'1920',bg:hex('#2A2014'),luz:hex('#E6C48F')},
 {nome:'Válvulas',anos:'1950–60',bg:hex('#2B1A08'),luz:hex('#FF9A3C')},
 {nome:'Fósforo',anos:'1970–80',bg:hex('#07200F'),luz:hex('#3DDC7A')},
 {nome:'Pixels',anos:'1990–2000',bg:hex('#1B0A26'),luz:hex('#FF5FE0')},
 {nome:'Vidro',anos:'2010–2026',bg:hex('#0A1A2E'),luz:hex('#7DB8F0')}];
let bgC=ERAS[0].bg.slice(), luzC=ERAS[0].luz.slice();
const mix=(a,b,f)=>a.map((v,i)=>Math.round(v+(b[i]-v)*f));
let eUlt=-9;
function setEra(v){
  v=Math.round(Math.max(0,Math.min(4,v))*40)/40; if(v===eUlt) return; eUlt=v;
  e=v; const i=Math.min(3,Math.floor(e)), f=e-i;
  bgC=mix(ERAS[i].bg,ERAS[i+1].bg,f); luzC=mix(ERAS[i].luz,ERAS[i+1].luz,f);
  S.setProperty('--bg',`rgb(${bgC})`); S.setProperty('--bg-rgb',bgC.join(','));
  S.setProperty('--luz',`rgb(${luzC})`); S.setProperty('--luz-rgb',luzC.join(','));
  const n=Math.round(e); const hud=$('#hb-hud-ano'); if(hud){const t=ERAS[n].anos+' · '+ERAS[n].nome; if(hud.textContent!==t) hud.textContent=t;}
}

/* ---------- grão de filme (tile gerado em canvas, sem arquivo) ---------- */
(()=>{const c=document.createElement('canvas');c.width=c.height=160;const x=c.getContext('2d'),d=x.createImageData(160,160);
 for(let i=0;i<d.data.length;i+=4){const v=Math.random()*255|0;d.data[i]=d.data[i+1]=d.data[i+2]=v;d.data[i+3]=255}
 x.putImageData(d,0,0);$('#hb-grao').style.backgroundImage=`url(${c.toDataURL('image/png')})`})();

/* ---------- silhuetas do meio (parallax 0,5x), geradas por código ---------- */
(()=>{
 const SV=[
  '<g fill="currentColor"><rect x="30" y="140" width="90" height="60"/><rect x="45" y="100" width="14" height="40"/><rect x="80" y="85" width="14" height="55"/><rect x="130" y="120" width="120" height="80"/><rect x="150" y="80" width="12" height="40"/><rect x="190" y="95" width="12" height="25"/></g><g fill="none" stroke="currentColor"><circle cx="330" cy="140" r="46" stroke-width="12" stroke-dasharray="14 11"/><circle cx="330" cy="140" r="26" stroke-width="6"/><circle cx="410" cy="170" r="26" stroke-width="8" stroke-dasharray="9 8"/></g>',
  '<g fill="currentColor">'+[0,1,2,3,4,5].map(i=>`<rect x="${20+i*62}" y="60" width="52" height="140" rx="3"/>`).join('')+'</g><g fill="#000" fill-opacity=".45">'+[0,1,2,3,4,5].map(i=>`<circle cx="${46+i*62}" cy="100" r="14"/><circle cx="${46+i*62}" cy="146" r="14"/>`).join('')+'</g>',
  '<g fill="currentColor"><rect x="30" y="90" width="120" height="86" rx="10"/><rect x="60" y="176" width="60" height="14"/><rect x="20" y="192" width="140" height="8" rx="2"/><rect x="200" y="120" width="96" height="66" rx="8"/><rect x="222" y="186" width="52" height="10"/><rect x="330" y="70" width="110" height="100" rx="12"/></g><g fill="#000" fill-opacity=".45"><rect x="42" y="102" width="96" height="62" rx="4"/><rect x="210" y="130" width="76" height="46" rx="3"/><rect x="342" y="82" width="86" height="76" rx="4"/></g>',
  null,
  '<g fill="currentColor"><rect x="20" y="70" width="150" height="70" rx="22"/><path d="M50 140 L48 164 L78 140Z"/><rect x="200" y="110" width="120" height="58" rx="20"/><path d="M290 168 L300 190 L270 168Z"/><circle cx="380" cy="90" r="40"/><circle cx="430" cy="150" r="22"/></g>'];
 const pix=[];let seed=7;const rnd=()=>(seed=(seed*16807)%2147483647)/2147483647;
 for(let i=0;i<16;i++){const h=2+Math.floor(rnd()*9);for(let j=0;j<h;j++)pix.push(`<rect x="${14+i*28}" y="${192-j*16}" width="22" height="12"/>`)}
 SV[3]='<g fill="currentColor">'+pix.join('')+'</g>';
 $$('#hb-c-meio>.hb-e').forEach((c,i)=>{c.innerHTML=`<svg viewBox="0 0 480 200" preserveAspectRatio="xMidYMax slice" aria-hidden="true">${SV[i]}</svg>`});
})();

/* ---------- névoa: shader de ruído em meia resolução (alternativa 2D) ---------- */
const at=$('#hb-atmos'), cv=$('#hb-nevoa'), poca=$('#hb-poca');
let gl=null,P=null,U={},ctx2=null,escala=.22,ema=16.7,tPrev=0;
const VS='attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}';
const FS=`precision mediump float;
uniform vec2 uRes;uniform float uT,uR,uDens;uniform vec2 uM;uniform vec3 uCor,uLuz;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1.,0.)),f.x),mix(h(i+vec2(0.,1.)),h(i+vec2(1.,1.)),f.x),f.y);}
float fbm(vec2 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*n(p);p=p*2.03+vec2(1.7,9.2);a*=.5;}return s;}
void main(){
 vec2 uv=gl_FragCoord.xy/uRes;float asp=uRes.x/uRes.y;vec2 p=vec2(uv.x*asp,uv.y);
 vec2 q=p*2.4+vec2(uT*.035,-uT*.018);
 float f=fbm(q+vec2(uT*.02,0.));
 float d=clamp(.30+smoothstep(.22,.78,f)*.75,0.,1.)*uDens;
 vec2 m=vec2(uM.x*asp,uM.y);float dist=length(p-m);
 float edge=(f-.5)*1.6;
 float hole=smoothstep(uR*.40,uR*1.0,dist+edge*uR*.6);
 float a=d*hole;
 vec3 col=mix(uCor,uLuz,(1.-hole)*.55);
 gl_FragColor=vec4(col*a,a);
}`;
function initGL(){
  try{gl=cv.getContext('webgl',{alpha:true,premultipliedAlpha:true,antialias:false,powerPreference:'low-power'});}catch(_){gl=null}
  if(!gl){ctx2=cv.getContext('2d');return}
  const sh=(t,s)=>{const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))throw 0;return o};
  try{P=gl.createProgram();gl.attachShader(P,sh(gl.VERTEX_SHADER,VS));gl.attachShader(P,sh(gl.FRAGMENT_SHADER,FS));gl.linkProgram(P);gl.useProgram(P)}catch(_){gl=null;P=null;ctx2=null;return}
  const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  const l=gl.getAttribLocation(P,'a');gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,2,gl.FLOAT,false,0,0);
  ['uRes','uT','uR','uDens','uM','uCor','uLuz'].forEach(k=>U[k]=gl.getUniformLocation(P,k));
}
/* a névoa cobre a camada atmos (a janela inteira, ou o palco da faixa sob o cabeçalho) */
function caixa(){ const r=at.getBoundingClientRect(); return {l:r.left,t:r.top,w:r.width||innerWidth,h:r.height||innerHeight} }
function dimensiona(){
  const dpr=Math.min(devicePixelRatio||1,1.5), k=Math.min(escala,1)*dpr/1.5*1.5, c=caixa(); // meia resolução ou menos
  cv.width=Math.max(128,Math.round(c.w*k)); cv.height=Math.max(72,Math.round(c.h*k));
  if(gl) gl.viewport(0,0,cv.width,cv.height);
}
let TX=innerWidth*.6, TY=innerHeight*.4, LX=TX, LY=TY, vel=0;
function desenhaNevoa(t,R,c0){
  const w=cv.width,h=cv.height, mx=(LX-c0.l)/c0.w, my=1-(LY-c0.t)/c0.h;
  const cor=mix(luzC,bgC,.55).map(v=>v/255);
  if(gl){
    gl.uniform2f(U.uRes,w,h);gl.uniform1f(U.uT,t/1000);gl.uniform1f(U.uR,R);gl.uniform1f(U.uDens,innerWidth<900?.9:1.05);
    gl.uniform2f(U.uM,mx,my);gl.uniform3f(U.uCor,cor[0],cor[1],cor[2]);gl.uniform3f(U.uLuz,luzC[0]/255,luzC[1]/255,luzC[2]/255);
    gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,3);
  }else if(ctx2){
    const c=ctx2; c.globalCompositeOperation='source-over';c.clearRect(0,0,w,h);
    c.fillStyle=`rgba(${mix(luzC,bgC,.55)},.55)`;c.fillRect(0,0,w,h);
    for(let i=0;i<5;i++){const x=(Math.sin(t/9000+i*1.7)*.5+.5)*w,y=(Math.cos(t/11000+i*2.3)*.5+.5)*h;
      const g=c.createRadialGradient(x,y,0,x,y,h*.6);g.addColorStop(0,`rgba(${mix(luzC,bgC,.3)},.35)`);g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,w,h)}
    c.globalCompositeOperation='destination-out';
    const g=c.createRadialGradient(mx*w,(1-my)*h,0,mx*w,(1-my)*h,R*h);
    g.addColorStop(0,'rgba(0,0,0,1)');g.addColorStop(.6,'rgba(0,0,0,.9)');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,w,h);
  }
}

/* ---------- luz: sombra e brilho coerentes com a fonte ---------- */
let litEls=[];
function luzNosComponentes(){
  const vw=innerWidth,vh=innerHeight, rs=litEls.map(x=>x.getBoundingClientRect());
  for(let i=0;i<litEls.length;i++){
    const r=rs[i]; if(r.bottom<-240||r.top>vh+240||r.right<-240||r.left>vw+240) continue;
    const x=litEls[i], cx=r.left+r.width/2, cy=r.top+r.height/2, dx=cx-LX, dy=cy-LY, d=Math.hypot(dx,dy)||1;
    const m=5+20*Math.max(0,1-d/1100), s=x.style;
    s.setProperty('--sx',(dx/d*m).toFixed(1)+'px'); s.setProperty('--sy',(dy/d*m+3).toFixed(1)+'px');
    s.setProperty('--sb',Math.min(46,14+d/42).toFixed(0)+'px');
    if(x.classList.contains('hb-lit')){
      const ex=Math.max(r.left-LX,0,LX-r.right), ey=Math.max(r.top-LY,0,LY-r.bottom), de=Math.hypot(ex,ey);
      s.setProperty('--lx',(LX-r.left).toFixed(0)+'px'); s.setProperty('--ly',(LY-r.top).toFixed(0)+'px');
      s.setProperty('--li',Math.pow(Math.max(0,1-de/460),.8).toFixed(2));
    }
  }
}

/* ---------- loop principal (névoa + luz): pausa em aba oculta / pausado ---------- */
const faixa=$('#hb-faixa'), trilho=$('#hb-trilho'), cFundo=$('#hb-c-fundo'), cMeio=$('#hb-c-meio');
let raf=0,fcount=0;
function frame(t){
  raf=0; if(pausado||document.hidden) return;
  const dt=t-(tPrev||t); tPrev=t;
  if(dt>0&&dt<200){ema+=(dt-ema)*.06; // resolução adaptativa
    if(ema>22&&escala>.14){escala=Math.max(.14,escala*.85);ema=16.7;dimensiona()}}
  if(innerWidth<900){ // toque/390: a abertura segue o centro da tela ao rolar
    TX=innerWidth*(.5+.22*Math.sin(scrollY/380)); TY=innerHeight*(.46+.10*Math.cos(scrollY/520));
  }
  const px=LX,py=LY; LX+=(TX-LX)*.13; LY+=(TY-LY)*.13; vel+=((Math.hypot(LX-px,LY-py))-vel)*.1;
  const R=(innerWidth<900?.40:.27)+Math.min(.07,vel*.004)+.012*Math.sin(t/1400);
  const c0=caixa();
  if(((fcount++)&1)===0){ const fr=faixaOn?faixa.getBoundingClientRect():null; if(!fr||(fr.bottom>0&&fr.top<innerHeight)) desenhaNevoa(t,R,c0) }
  poca.style.transform=`translate3d(${(LX-c0.l).toFixed(0)}px,${(LY-c0.t).toFixed(0)}px,0)`;
  if((fcount&1)===0) luzNosComponentes();
  raf=requestAnimationFrame(frame);
}
function liga(){ if(!raf&&!pausado&&!document.hidden){tPrev=0;raf=requestAnimationFrame(frame)} }
addEventListener('pointermove',ev=>{ if(ev.pointerType==='touch'||innerWidth<900) return; TX=ev.clientX; TY=ev.clientY; },{passive:true});
document.addEventListener('visibilitychange',()=>{ if(document.hidden){ if(raf){cancelAnimationFrame(raf);raf=0} } else liga() });

/* ---------- scroll: faixa horizontal, parallax em 3 camadas, cor por década ---------- */
let agendado=false;
function aoRolar(){
  agendado=false;
  const vw=root.clientWidth, vh=innerHeight;
  if(faixaOn){
    const r=faixa.getBoundingClientRect(), total=faixa.offsetHeight-(vh-CAB);
    const p=total>0?Math.max(0,Math.min(1,(CAB-r.top)/total)):0;
    trilho.style.transform=`translate3d(${-p*(trilho.offsetWidth-vw)}px,0,0)`;
    cMeio.style.transform=`translate3d(${-p*(cMeio.offsetWidth-vw)}px,0,0)`;
    cFundo.style.transform=`translate3d(${-p*(cFundo.offsetWidth-vw)}px,0,0)`;
    const f=(p*(trilho.offsetWidth-vw)+vw/2)/trilho.offsetWidth; // fração do trilho sob o centro da tela
    setEra(f*5-.5); $('#hb-hud-barra').style.width=(p*100).toFixed(1)+'%';
  }else{
    const ers=$$('.hb-era',trilho), mid=vh/2, cs=ers.map(x=>{const b=x.getBoundingClientRect();return b.top+b.height/2});
    let v=0; if(mid>=cs[4]) v=4; else if(mid>cs[0]){let k=0;while(k<3&&mid>=cs[k+1])k++;v=k+(mid-cs[k])/(cs[k+1]-cs[k])}
    setEra(v);
  }
  if(pausado||reduzido) luzNosComponentes();
}
function agenda(){ if(!agendado){agendado=true;requestAnimationFrame(aoRolar)} }
function layout(){
  const on=!reduzido&&innerWidth>=900; faixaOn=on; root.classList.toggle('hb-faixa-on',on);
  const alvo=on?$('.hb-palco-fundo'):root; if(at.parentNode!==alvo){ if(on) alvo.appendChild(at); else alvo.prepend(at) }
  litEls=$$('.hb-lit,.hb-sombra-txt');
  if(!on){[trilho,cMeio,cFundo].forEach(x=>x.style.transform='')}
  if(!reduzido) dimensiona();
  if(reduzido){LX=innerWidth*.28;LY=innerHeight*.18;const c=caixa();poca.style.transform=`translate3d(${(LX-c.l).toFixed(0)}px,${(LY-c.t).toFixed(0)}px,0)`}
  aoRolar();
}
addEventListener('scroll',agenda,{passive:true}); addEventListener('resize',()=>{layout()});

/* ---------- botão pausar movimento ---------- */
const bt=$('#hb-pausa');
function rotulo(){ bt.textContent=reduzido?'movimento pausado (modo reduzido)':(pausado?'retomar movimento':'pausar movimento'); bt.setAttribute('aria-pressed',String(pausado)); root.classList.toggle('hb-pausado',pausado) }
if(reduzido) bt.disabled=true;
bt.addEventListener('click',()=>{ if(reduzido) return; pausado=!pausado; rotulo(); if(pausado){ if(raf){cancelAnimationFrame(raf);raf=0} } else liga() });
rotulo();

/* ---------- arranque ---------- */
if(!reduzido) initGL();
layout();
if(!reduzido) liga();
});
