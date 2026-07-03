from flask import Blueprint, render_template
from util.decorators import login_requerido

inicio_bp = Blueprint("inicio", __name__)

#----RUTA PRINCIPAL----
@inicio_bp.route("/inicio")
@login_requerido
def inicio():
    return render_template("inicio.html")