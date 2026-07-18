function confirmarAccion(opciones) {

    const modal = document.getElementById("confirmModal");

    const titulo = document.getElementById("tituloConfirmacion");
    const mensaje = document.getElementById("mensajeConfirmacion");
    const boton = document.getElementById("btnConfirmarAccion");
    const icono = document.getElementById("iconoConfirmacion");

    titulo.innerHTML = `
        <i id="iconoConfirmacion" class="bi bi-question-circle"></i>
        ${opciones.titulo}
    `;

    mensaje.innerHTML = opciones.mensaje;

    // Reiniciar clases del título
    titulo.classList.remove(
        "modal-title-success",
        "modal-title-danger",
        "modal-title-primary",
        "modal-title-warning"
    );

    // Reiniciar clases del botón
    boton.className = "btn btn-modal";

    switch(opciones.color){

        case "danger":

            titulo.classList.add("modal-title-danger");

            boton.classList.add("btn-modal-danger");

            boton.innerHTML = `
                <i class="bi bi-trash"></i>
                ${opciones.textoBoton}
            `;

            break;

        case "success":

            titulo.classList.add("modal-title-success");

            boton.classList.add("btn-modal-success");

            boton.innerHTML = `
                <i class="bi bi-check-circle"></i>
                ${opciones.textoBoton}
            `;

            break;

        case "warning":

            titulo.classList.add("modal-title-warning");

            boton.classList.add("btn-modal-primary");

            boton.innerHTML = `
                <i class="bi bi-exclamation-circle"></i>
                ${opciones.textoBoton}
            `;

            break;

        default:

            titulo.classList.add("modal-title-primary");

            boton.classList.add("btn-modal-primary");

            boton.innerHTML = opciones.textoBoton;

    }

    boton.onclick = function(){

        bootstrap.Modal.getInstance(modal).hide();

        if(typeof opciones.onConfirm === "function"){

            opciones.onConfirm();

        }

    };

    new bootstrap.Modal(modal).show();

}