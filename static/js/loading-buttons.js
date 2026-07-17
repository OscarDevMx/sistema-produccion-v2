/**
 * Activa el comportamiento de botones con indicador de carga.
 *
 * Requisitos:
 * - El botón debe tener la clase: btn-loading
 * - Puede personalizar el texto con:
 *   data-loading-text="Guardando..."
 *
 * Ejemplo:
 * <button
 *     type="submit"
 *     class="btn btn-success btn-loading"
 *     data-loading-text="Guardando...">
 *     Guardar
 * </button>
 */

function activarBotonesDeCarga() {

    document.querySelectorAll("form").forEach(form => {

        form.addEventListener("submit", function () {

            const boton = document.activeElement;

            if (!boton || !boton.classList.contains("btn-loading")) {
                return;
            }

            boton.disabled = true;

            boton.dataset.textoOriginal = boton.innerHTML;

            const textoCarga =
                boton.dataset.loadingText || "Guardando...";

            boton.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2"></span>
                ${textoCarga}
            `;

        });

    });

}