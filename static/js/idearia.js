/*
 * Idearia - comportamiento general de la interfaz.
 * Solo mejora la experiencia: TODAS las validaciones importantes
 * se repiten en el servidor (Django Forms).
 */
(function () {
  "use strict";

  // 1. Confirmación antes de acciones importantes: <form data-confirmar="¿Seguro?">
  document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      if (!window.confirm(form.dataset.confirmar)) {
        evento.preventDefault();
      }
    });
  });

  // 2. Contador de caracteres para campos con maxlength
  document.querySelectorAll("textarea[maxlength], input[maxlength][data-contador]").forEach(function (campo) {
    var maximo = parseInt(campo.getAttribute("maxlength"), 10);
    var contador = document.createElement("span");
    contador.className = "contador-caracteres";
    contador.setAttribute("aria-live", "polite");
    campo.insertAdjacentElement("afterend", contador);
    function actualizar() {
      contador.textContent = campo.value.length + "/" + maximo;
      contador.classList.toggle("excedido", campo.value.length >= maximo);
    }
    campo.addEventListener("input", actualizar);
    actualizar();
  });

  // 3. Mostrar / ocultar contraseña
  document.querySelectorAll("[data-alternar-clave]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var campo = document.getElementById(boton.dataset.alternarClave);
      if (!campo) return;
      var visible = campo.type === "text";
      campo.type = visible ? "password" : "text";
      boton.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
    });
  });

  // 4. Archivo seleccionado: muestra el nombre y avisa si es muy grande o de otro formato
  document.querySelectorAll("input[type=file][data-max-mb]").forEach(function (campo) {
    var aviso = document.getElementById(campo.dataset.aviso);
    campo.addEventListener("change", function () {
      if (!aviso) return;
      var archivo = campo.files[0];
      if (!archivo) { aviso.textContent = "Ningún archivo seleccionado"; return; }
      var maxBytes = parseFloat(campo.dataset.maxMb) * 1024 * 1024;
      var extension = archivo.name.split(".").pop().toLowerCase();
      var permitidas = (campo.getAttribute("accept") || "").replace(/\./g, "").split(",");
      var mensaje = "Seleccionado: " + archivo.name + " (" + (archivo.size / 1024 / 1024).toFixed(2) + " MB)";
      if (permitidas[0] && permitidas.indexOf(extension) === -1) {
        mensaje = "Formato no permitido (." + extension + ").";
      } else if (archivo.size > maxBytes) {
        mensaje = "El archivo supera " + campo.dataset.maxMb + " MB.";
      }
      aviso.textContent = mensaje;
    });
  });

  // 5. Cerrar mensajes
  document.querySelectorAll(".cerrar-alerta").forEach(function (boton) {
    boton.addEventListener("click", function () {
      boton.closest(".alerta").remove();
    });
  });

  // 6. Visor de planificaciones: sin menú contextual, copiar ni arrastrar (medida disuasiva)
  document.querySelectorAll(".visor-marco").forEach(function (marco) {
    ["contextmenu", "copy", "dragstart"].forEach(function (evento) {
      marco.addEventListener(evento, function (e) { e.preventDefault(); });
    });
  });

  // 7. En pantallas pequeñas, el panel de filtros parte cerrado para ver primero los resultados
  if (window.matchMedia("(max-width: 960px)").matches) {
    document.querySelectorAll("details[data-cerrar-en-movil]").forEach(function (panel) {
      panel.open = false;
    });
  }

  // 8. Enviar el formulario de orden al cambiar la opción
  document.querySelectorAll("select[data-enviar-al-cambiar]").forEach(function (select) {
    select.addEventListener("change", function () {
      select.form.submit();
    });
  });
})();
