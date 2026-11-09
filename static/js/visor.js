/*
 * Visor de planificaciones PDF dentro de Idearia.
 *
 * Usa PDF.js para dibujar cada página en un <canvas>. Así el documento se
 * lee dentro de la plataforma SIN la barra del visor del navegador
 * (que incluye el botón "Descargar").
 *
 * El servidor solo entrega el PDF si la petición trae la cabecera
 * X-Idearia-Visor; escribir la URL directamente en el navegador da 403.
 * Esto reduce la distribución directa, aunque ningún método web puede
 * impedir al 100 % una captura de pantalla.
 */
(function () {
  "use strict";

  var contenedor = document.getElementById("visor-pdf");
  if (!contenedor) return;
  var estado = document.getElementById("visor-estado");

  function mostrarEstado(texto) {
    if (estado) estado.textContent = texto;
  }

  if (!window.pdfjsLib) {
    mostrarEstado("No fue posible cargar el visor de documentos.");
    return;
  }

  window.pdfjsLib.GlobalWorkerOptions.workerSrc = contenedor.dataset.worker;

  var tarea = window.pdfjsLib.getDocument({
    url: contenedor.dataset.url,
    httpHeaders: { "X-Idearia-Visor": "1" },
    withCredentials: true,
    isEvalSupported: false,
    disableRange: true,
    disableStream: true,
  });

  tarea.promise
    .then(function (pdf) {
      mostrarEstado("Cargando " + pdf.numPages + " página(s)...");
      var cadena = Promise.resolve();
      for (var numero = 1; numero <= pdf.numPages; numero++) {
        cadena = cadena.then(dibujarPagina.bind(null, pdf, numero));
      }
      return cadena.then(function () {
        mostrarEstado(pdf.numPages + " página(s) · Visualización exclusiva en Idearia");
      });
    })
    .catch(function () {
      mostrarEstado("No fue posible mostrar la planificación. Intenta nuevamente más tarde.");
    });

  function dibujarPagina(pdf, numero) {
    return pdf.getPage(numero).then(function (pagina) {
      var anchoDisponible = Math.min(contenedor.clientWidth || 800, 900);
      var vistaBase = pagina.getViewport({ scale: 1 });
      var escala = anchoDisponible / vistaBase.width;
      var densidad = window.devicePixelRatio || 1;
      var vista = pagina.getViewport({ scale: escala * densidad });

      var canvas = document.createElement("canvas");
      canvas.width = vista.width;
      canvas.height = vista.height;
      canvas.style.width = Math.floor(vista.width / densidad) + "px";
      canvas.setAttribute("aria-label", "Página " + numero);
      contenedor.appendChild(canvas);

      return pagina.render({ canvasContext: canvas.getContext("2d"), viewport: vista }).promise;
    });
  }
})();
