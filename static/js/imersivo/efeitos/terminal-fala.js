import { registar } from "../motor.js";

// Terminal que escreve letra a letra quando o ato entra em vista. O texto completo
// já está no HTML (sem JS, ou com movimento reduzido, fica tudo legível e estático).
// A voz é opt-in: só fala depois de um clique em «Ouvir» (síntese do próprio navegador).
registar("terminal:fala", ({ el, parametros, reduzido }) => {
  const pre = el.querySelector("pre[data-terminal]");
  if (!pre) throw new Error("terminal ausente");
  const texto = pre.textContent;
  if ("speechSynthesis" in window && typeof SpeechSynthesisUtterance === "function") {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "im-ouvir";
    botao.textContent = "Ouvir";
    botao.addEventListener("click", () => {
      window.speechSynthesis.cancel();
      const fala = new SpeechSynthesisUtterance(texto);
      fala.lang = "pt-BR";
      window.speechSynthesis.speak(fala);
    });
    pre.parentElement.appendChild(botao);
  }
  if (reduzido) return;
  const ms = typeof parametros.velocidade === "number" ? parametros.velocidade : 45;
  let n = 0;
  pre.textContent = "";
  const passo = () => {
    n += 1;
    pre.textContent = texto.slice(0, n);
    if (n < texto.length) setTimeout(passo, ms);
  };
  passo();
});
