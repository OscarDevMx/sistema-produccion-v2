// ==========================
// Toast Notifications Premium
// ==========================

function mostrarToast({
    tipo = "info",
    titulo = "",
    mensaje = "",
    duracion = 3500
}) {

    let contenedor = document.querySelector(".toast-container-custom");

    if (!contenedor) {

        contenedor = document.createElement("div");
        contenedor.className = "toast-container-custom";

        document.body.appendChild(contenedor);

    }

    const iconos = {

        success: "bi-check-circle-fill",

        danger: "bi-x-circle-fill",

        warning: "bi-exclamation-triangle-fill",

        info: "bi-info-circle-fill"

    };

    const toast = document.createElement("div");

    toast.className = `toast-custom toast-${tipo}`;

    toast.innerHTML = `

        <div class="toast-header-custom">

            <i class="bi ${iconos[tipo]} toast-icon"></i>

            <span>${titulo}</span>

        </div>

        <div class="toast-body-custom">

            ${mensaje}

        </div>

        <div class="toast-progress">

            <div
                class="toast-progress-bar"
                style="animation-duration:${duracion}ms">
            </div>

        </div>

    `;

    contenedor.appendChild(toast);

    setTimeout(() => {

        toast.classList.add("toast-hide");

        setTimeout(() => {

            toast.remove();

        },300);

    },duracion);

}