from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modelos import User
from werkzeug.security import check_password_hash
from util.decorators import login_requerido

auth = Blueprint("auth", __name__)


# LOGIN
@auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        password = request.form.get("password")

        user = User.query.filter_by(nombre=nombre).first()

        if user and user.check_password(password):
            session["usuario"] = user.nombre
            flash(f"✅ Bienvenid@ {user.nombre}", "success")
            return redirect(url_for("inicio.inicio"))  # lo ajustamos después
        else:
            flash("❌ Usuario o contraseña incorrectos", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# LOGOUT
@auth.route("/logout")
def logout():
    usuario = session.pop("usuario", None)
    flash(f"👋 {usuario} cerró sesión." if usuario else "Ningún usuario activo.", "info")
    return redirect(url_for("auth.login"))