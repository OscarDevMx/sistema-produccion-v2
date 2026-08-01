from flask import Blueprint, render_template
from util.decorators import login_requerido
from services.dashboard_service import obtener_dashboard

inicio_bp = Blueprint("inicio", __name__)

#----RUTA PRINCIPAL----
@inicio_bp.route("/inicio")
@login_requerido
def inicio():

    dashboard = obtener_dashboard()
    return render_template(       
        "inicio.html",
        dashboard=dashboard)