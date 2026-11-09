import { registar } from "../motor.js";

// Convite do hub: a prévia do placar, a grelha dos posts e a tabela são
// markup estático; o JS só marca o ato como pronto (a tabela equivalente fica
// por CSS com movimento reduzido). Não há animação a ligar nem a desligar.
registar("grelha:posts", ({ el }) => {
  el.classList.add("im-convite--pronto");
});
