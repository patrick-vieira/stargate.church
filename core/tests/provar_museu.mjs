import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const modulo = async nome => import('data:text/javascript;base64,' + Buffer.from(readFileSync(process.argv[1] + '/' + nome, 'utf8')).toString('base64'));
const {criarModelo, TIPOS} = await modulo('modelo.js');
const {htmlSobrio} = await modulo('sobrio.js');
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
console.log('FLUXO 21→27: OK (lúdico e sóbrio)');
