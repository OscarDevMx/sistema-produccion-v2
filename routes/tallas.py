from flask import Blueprint, render_template, request, redirect, url_for, flash
from modelos import db, Talla
from util.decorators import login_requerido

tallas = Blueprint("tallas", __name__)


# ---- RUTA PARA GESTIONAR TALLAS ----
@tallas.route("/tallas", methods=["GET", "POST"])
@login_requerido
def gestionar_tallas():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()

        if nombre:
            # Validar si ya existe
            talla_existente = Talla.query.filter_by(nombre=nombre).first()
            if talla_existente:
                flash("⚠️ La talla ya existe, intenta con otro nombre.", "warning")
            else:
                try:
                    nueva_talla = Talla(nombre=nombre)
                    db.session.add(nueva_talla)
                    db.session.commit()
                    flash("✅ Talla agregada con éxito", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error al agregar la talla: {str(e)}", "danger")
        else:
            flash("⚠️ El nombre no puede estar vacío.", "danger")

        return redirect(url_for("tallas.gestionar_tallas"))

    tallas = Talla.query.all()
    return render_template("tallas.html", tallas=tallas)


# ---- RUTA PARA ELIMINAR TALLA ----
@tallas.route("/tallas/eliminar/<int:id>")
def eliminar_talla(id):
    talla = Talla.query.get_or_404(id)

    # Verificar si tiene cortes asociados
    if talla.producciones and len(talla.producciones) > 0:
        flash("⚠️ No se puede eliminar la talla porque tiene cortes asociados.", "danger")
    else:
        try:
            db.session.delete(talla)
            db.session.commit()
            flash("✅ Talla eliminada con éxito.", "info")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al eliminar la talla: {str(e)}", "danger")

    return redirect(url_for("tallas.gestionar_tallas"))


# RUTA PARA EDITAR TALLA
@tallas.route('/editar_talla/<int:id>', methods=['GET', 'POST'])
def editar_talla(id):
    talla = Talla.query.get_or_404(id)

    if request.method == 'POST':
        nuevo_nombre = request.form['nombre'].strip()

        # Validar que no exista otra talla con el mismo nombre
        existente = Talla.query.filter(
            Talla.nombre == nuevo_nombre,
            Talla.id != id
        ).first()
      
        if existente:
            flash('⚠️Ya existe una talla con ese nombre.', 'danger')
            return redirect(url_for('tallas.editar_talla', id=id))

        try:
            talla.nombre = nuevo_nombre
            db.session.commit()
            flash('✅ Talla actualizada correctamente.', 'success')
            return redirect(url_for('tallas.editar_talla', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar la talla: {str(e)}', 'error')
            return redirect(url_for('tallas.editar_talla', id=id))

    return render_template('editar_talla.html', talla=talla)