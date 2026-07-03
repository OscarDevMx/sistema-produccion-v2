from functools import wraps
from flask import session, flash, redirect, url_for


# DECORADOR GLOBAL
def login_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if "usuario" not in session:
            flash("⚠️ Debes iniciar sesión para acceder a esta sección.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorador