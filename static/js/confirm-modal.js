function confirmarAccion(opciones) {

    const modal = document.getElementById("confirmModal");

    document.getElementById("confirmModalTitle").innerHTML =
        opciones.titulo;

    document.getElementById("confirmModalMessage").innerHTML =
        opciones.mensaje;

    const btn = document.getElementById("confirmModalBtn");

    btn.className = "btn";

    btn.classList.add(
        opciones.color === "danger"
            ? "btn-danger"
            : "btn-success"
    );

    btn.innerHTML = opciones.textoBoton;

    btn.onclick = function () {

        bootstrap.Modal.getInstance(modal).hide();

        if (typeof opciones.onConfirm === "function") {
            opciones.onConfirm();
        }

    };

    new bootstrap.Modal(modal).show();

}