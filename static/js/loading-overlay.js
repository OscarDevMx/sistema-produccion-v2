function mostrarOverlay(mensaje = "Procesando información...") {

    let overlay = document.getElementById("loadingOverlay");

    if (!overlay) {

        overlay = document.createElement("div");
        overlay.id = "loadingOverlay";

        overlay.innerHTML = `
            <div class="loading-overlay-content">

                <div class="spinner-border text-primary mb-3"
                    style="width:3rem;height:3rem;"
                    role="status">
                </div>

                <h5 id="loadingOverlayText">${mensaje}</h5>

                <p class="loading-overlay-subtitle">
                    Por favor espere unos segundos...
                </p>

            </div>
        `;

        document.body.appendChild(overlay);
    }

    document.getElementById("loadingOverlayText").textContent = mensaje;

    overlay.style.display = "flex";
}


function ocultarOverlay() {

    const overlay = document.getElementById("loadingOverlay");

    if (overlay) {
        overlay.style.display = "none";
    }

}