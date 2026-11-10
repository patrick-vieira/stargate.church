import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const modulo = async nome => import('data:text/javascript;base64,' + Buffer.from(readFileSync(process.argv[1] + '/' + nome, 'utf8')).toString('base64'));
const {criarModelo, TIPOS} = await modulo('modelo.js');
const {htmlSobrio} = await modulo('sobrio.js');
const {criarSom, pintarInterruptorSom} = await modulo('som.js');
const ligacoes = {seguir: null, aprofundar: null, subir: null, otimista: null, catastrofico: null};
const dados = {series: [{slug: 'ficticia', titulo: 'Fictícia', episodios: []}], noticias: [], grafo: {serie: 'ficticia', titulo: 'Fictícia', entrada: 21, salas: [], visitas: [], nos: [
{id: 21, titulo: 'Entrada', texto: ['Texto'], nivel: 0, polo: 0, ligacoes: {...ligacoes, seguir: 22, museu: 27}, rotulos: {museu: 'Explorar as peças do museu'}},
{id: 22, titulo: 'Editorial', texto: ['Texto'], nivel: 0, polo: 0, ligacoes: {...ligacoes, seguir: 21}},
{id: 27, titulo: 'Guia', texto: ['Texto'], nivel: 0, polo: 0, ligacoes: {...ligacoes, seguir: 21}}
]}};
assert.deepEqual(TIPOS.slice(0, 5), ['seguir', 'aprofundar', 'subir', 'otimista', 'catastrofico']);
const modelo = criarModelo(dados);
const pos = {no: '21', vindo: []};
assert.equal(modelo.escolha(pos, 'seguir').alvo, '22');
assert.equal(modelo.escolha(pos, 'museu').texto, 'Explorar as peças do museu');
assert.equal(modelo.ir(pos, 'museu').no, '27');
const html = htmlSobrio(dados);
assert.match(html, /href="#n27" data-tipo="museu">Explorar as peças do museu<\/a>/);
assert.match(html, /href="#n22" data-tipo="seguir"/);
dados.grafo.nos[0].narracao = 'Narração fictícia';
dados.grafo.nos[0].narracao_audio_endpoint = '/museu/ficticia/audio/21/narracao/';
assert.match(htmlSobrio(dados), /data-audio-endpoint="\/museu\/ficticia\/audio\/21\/narracao\/">Ouvir a narração/);

let consultas = 0, audios = [];
globalThis.fetch = async () => {
  consultas++;
  return {ok: true, json: async () => ({url: 'https://media.invalid/audio.mp3'})};
};
globalThis.Audio = class {
  constructor(src) { this.src = src; this.paradas = 0; audios.push(this); }
  play() { return Promise.resolve(); }
  pause() { this.paradas++; }
  removeAttribute() {}
  load() {}
};
const som = criarSom();
assert.equal(som.ligado, false);
const atributosSwitch = {};
const rotuloSwitch = {textContent: ''};
const switchSom = {
  setAttribute: (nome, valor) => { atributosSwitch[nome] = valor; },
  querySelector: () => rotuloSwitch,
};
som.ligar(true);
pintarInterruptorSom(switchSom, som.ligado);
assert.equal(atributosSwitch['aria-checked'], 'true');
assert.equal(rotuloSwitch.textContent, 'Som: ligado');
som.ligar(false);
pintarInterruptorSom(switchSom, som.ligado);
assert.equal(atributosSwitch['aria-checked'], 'false');
assert.equal(rotuloSwitch.textContent, 'Som: desligado');
await som.ambiente('/ambiente');
assert.equal(consultas, 0, 'não deve iniciar sem opt-in');
som.ligar(true);
await som.ambiente('/ambiente');
assert.equal(consultas, 1);
await som.narrar('/narracao');
assert.ok(audios[0].paradas > 0, 'a narração interrompe o som ambiente');
som.ligar(false);
assert.ok(audios[1].paradas > 0, 'desligar interrompe a narração');
console.log('FLUXO 21→27: OK (lúdico e sóbrio)');
