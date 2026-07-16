function activarBotonesDeCarga() {

    document.querySelectorAll("form").forEach(form => {

        form.addEventListener("submit", function () {

            const boton = form.querySelector(".btn-loading");

            if (!boton) return;

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