/* Cola servidor → luz (STAR-54). O formulário de conta faz POST completo e o servidor re-renderiza com .sg-erro[role=alert].
   Aqui só se traduz isso para a luz: marca os campos com erro (aria-invalid) e dispara o tremor do cartão. Sem erro, não faz nada. */
(function () {
  'use strict';
  function aoCarregar() {
    var cartoes = document.querySelectorAll('[data-luz=nevoa]');
    Array.prototype.forEach.call(cartoes, function (cartao) {
      if (!cartao.querySelector('.sg-erro[role=alert]')) return;
      Array.prototype.forEach.call(cartao.querySelectorAll('input[aria-describedby]'), function (campo) {
        var ids = campo.getAttribute('aria-describedby').split(/\s+/);
        var comErro = ids.some(function (id) {
          var alvo = id && document.getElementById(id);
          return alvo && alvo.classList.contains('sg-erro');
        });
        if (comErro) campo.setAttribute('aria-invalid', 'true');
      });
      if (window.Luz && window.Luz.erro) window.Luz.erro(cartao);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', aoCarregar);
  else aoCarregar();
})();
