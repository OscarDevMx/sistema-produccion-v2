from flask import Blueprint, app, render_template, request, redirect, url_for, flash
from modelos import db, Color
from util.decorators import login_requerido

catalogos = Blueprint("catalogos", __name__)

#---RUTA PARA GESTIONAR COLORES----
@catalogos.route("/colores", methods=["GET", "POST"])
def gestionar_colores():
    if request.method == "POST":
        nombre = request.form["nombre"].strip().capitalize()

        if nombre:
            # Verificar si ya existe un color con ese nombre
            color_existente = Color.query.filter_by(nombre=nombre).first()
            if color_existente:
                flash("⚠️ El color ya existe, intenta con otro nombre.", "warning")
            else:
                try:
                    nuevo_color = Color(nombre=nombre)
                    db.session.add(nuevo_color)
                    db.session.commit()
                    flash("✅ Color agregado con éxito", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error al agregar el color: {str(e)}", "danger")
        else:
            flash("⚠️ El nombre no puede estar vacío.", "danger")

        return redirect(url_for("catalogos.gestionar_colores"))

    colores = Color.query.all()
    return render_template("colores.html", colores=colores)


#----RUTA PARA ELIMINAR COLOR CON VALIDACIÓN DE ASOCIACIONES----
@catalogos.route("/colores/eliminar/<int:id>")
def eliminar_color(id):
    color = Color.query.get_or_404(id)
    
    if color.cortes:  # Revisamos si hay cortes asociados
        flash(
            f"No se puede eliminar el color '{color.nombre}' porque tiene cortes asociados.",
            "warning"
        )
    elif color.inventarios:  # Revisamos si hay inventarios asociados
        flash(
            f"No se puede eliminar el color '{color.nombre}' porque tiene inventarios asociados.",
            "warning"
        )
    else:
        try:
            db.session.delete(color)
            db.session.commit()
            flash(f"Color '{color.nombre}' eliminado con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al eliminar el color: {str(e)}", "danger")

    return redirect(url_for("catalogos.gestionar_colores"))  # Ajusta a la ruta que uses para listar colores


# RUTA PARA EDITAR COLOR
@catalogos.route("/editar_color/<int:id>", methods=["GET", "POST"])
def editar_color(id):
    color = Color.query.get_or_404(id)

    if request.method == "POST":
        nuevo_nombre = request.form.get("nombre", "").strip().capitalize()
        if not nuevo_nombre:
            flash("El nombre del color no puede estar vacío.", "warning")
            return redirect(url_for("catalogos.gestionar_colores"))

        # Verificar si el nombre ha cambiado
        if color.nombre == nuevo_nombre:
            flash("No se realizaron cambios.", "info")
            return redirect(url_for("catalogos.gestionar_colores"))

        # Revisar si ya existe otro color con el mismo nombre
        color_existente = Color.query.filter(Color.nombre == nuevo_nombre, Color.id != id).first()
        if color_existente:
            flash(f"Ya existe un color con el nombre '{nuevo_nombre}'.", "danger")
            return redirect(url_for("catalogos.gestionar_colores"))

        try:
            color.nombre = nuevo_nombre
            db.session.commit()
            flash(f"Color actualizado correctamente a '{nuevo_nombre}'.", "success")
            return redirect(url_for("catalogos.gestionar_colores")) # Ajusta a tu ruta de lista de colores
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al actualizar el color: {str(e)}", "danger")
            return redirect(url_for("catalogos.gestionar_colores"))

    return render_template("editar_color.html", color=color)
