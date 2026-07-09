
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify, abort, send_file, make_response
from extensions import db
from modelos import (
    Color,
    Talla,
    Corte,
    Produccion,
    Status,
    HistorialProduccion,
    User,
    Inventario,
    HistorialInventario,
    HistorialSalidas,
    Pedido,
    PedidoDetalle,
    StatusPedido,
    HistorialPedidos,
)
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from utils import fecha_local_tijuana
from zoneinfo import ZoneInfo
from sqlalchemy import func, extract
from sqlalchemy import desc
import json
import os

from sqlalchemy import and_
from config import Config
from routes.auth import auth
from util.decorators import login_requerido
from routes.inicio import inicio_bp
from routes.catalogos import catalogos
from routes.tallas import tallas

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(inicio_bp)
app.register_blueprint(catalogos)
app.register_blueprint(tallas)

with app.app_context():
    db.create_all()

    # 👇 Inicializar tabla Status solo si está vacía
    if not Status.query.first():
        estados = [
            Status(nombre="Cortadas", descripcion="Playeras cortadas pero no cosidas", fase="Producción"),
            Status(nombre="Cosidas", descripcion="Playeras ya cosidas", fase="Producción"),
            Status(nombre="Dobladas", descripcion="Playeras volteadas y dobladas", fase="Producción"),
            Status(nombre="Enviadas_a_Inventario", descripcion="Playeras enviadas a inventario", fase="Producción"),

            Status(nombre="En_Inventario", descripcion="Playeras disponibles en inventario para venta", fase="Inventario"),
            Status(nombre="Reparadas", descripcion="Playeras reparadas y listas para inventario", fase="Inventario"),
            Status(nombre="Devueltas", descripcion="Playeras devueltas por el cliente", fase="Inventario"),
            Status(nombre="Perdidas", descripcion="Playeras extraviadas", fase="Inventario"),
            Status(nombre="Donadas", descripcion="Playeras donadas", fase="Inventario"),            
            Status(nombre="Dañadas", descripcion="Playeras defectuosas", fase="Inventario"),
            Status(nombre="Ajuste_Baja", descripcion="Playeras eliminadas por ajuste", fase="Inventario"),
            Status(nombre="Apartadas", descripcion="Playeras apartadas en preventa", fase="Inventario"),
            Status(nombre="Surtidas", descripcion="Playeras surtidas al cliente", fase="Inventario"),
            Status(nombre="Vendidas", descripcion="Playeras vendidas al cliente", fase="Inventario"),        
        ]
        db.session.add_all(estados)
        db.session.commit()
        print("✅ Estados iniciales cargados en la base de datos")
    else:
        print("ℹ️ Estados ya existen, no se insertaron duplicados")

    # 👇 Inicializar tabla Status solo si está vacía
    if not StatusPedido.query.first():
        estados = [
            StatusPedido(nombre="Pendiente", descripcion="Pedido pendiente de surtir"),
            StatusPedido(nombre="Apartado", descripcion="Pedido apartado en preventa"),
            StatusPedido(nombre="Parcial", descripcion="Pedido parcialmente surtido al cliente"),
            StatusPedido(nombre="Surtido", descripcion="Pedido surtido al cliente"),
            StatusPedido(nombre="Vendido", descripcion="Pedido vendido al cliente"),
            StatusPedido(nombre="Cancelado", descripcion="Pedido cancelado"),            
        ]
        db.session.add_all(estados)
        db.session.commit()
        print("✅ Estados iniciales cargados en la base de datos")
    else:
        print("ℹ️ Estados ya existen, no se insertaron duplicados")

    # 👇 Inicializar tabla Talla solo si está vacía
    if not Talla.query.first():
        Tallas = [
            Talla(nombre="0", costo=45),
            Talla(nombre="2", costo=45),
            Talla(nombre="4", costo=45),
            Talla(nombre="6", costo=45),
            Talla(nombre="8", costo=50),
            Talla(nombre="10", costo=50),
            Talla(nombre="12", costo=50),
        ]
        db.session.add_all(Tallas)
        db.session.commit()
        print("✅ Tallas iniciales cargados en la base de datos")
    else:
        print("ℹ️ Tallas ya existen, no se insertaron duplicados")

    # Inicializar Usuarios
    if not User.query.first():
        usuarios_iniciales = [
            {"nombre": "Vicky", "rol": "Produccion", "password": "020525"},
            {"nombre": "Alberto", "rol": "Inventarios", "password": "050925"},
            {"nombre": "Oscar", "rol": "Ventas", "password": "240825"}
        ]

        for usuario_data in usuarios_iniciales:
            existente = User.query.filter_by(nombre=usuario_data["nombre"]).first()
            if not existente:
                nuevo_usuario = User(
                    nombre=usuario_data["nombre"],
                    rol=usuario_data["rol"],
                    password_hash=generate_password_hash(usuario_data["password"])
                )
                db.session.add(nuevo_usuario)
                print(f"✅ Usuario agregado: {usuario_data['nombre']}")
        db.session.commit()
        print("✅ Usuarios iniciales cargados en la base de datos")
    else:
        print("ℹ️ Usuarios ya existen, no se insertaron duplicados")

def obtener_status_id(nombre_status):
    status = Status.query.filter_by(nombre=nombre_status).first()
    return status.id if status else None

#----PAGINA DE CORTES----

@app.route("/cortes", methods=["GET"])
@login_requerido
def cortes():
    colores = Color.query.all()
    tallas = Talla.query.all()
    fecha_hoy = date.today().strftime("%Y-%m-%d")
    return render_template("cortes.html", colores=colores, tallas=tallas, fecha_hoy=fecha_hoy)


#----RUTA PARA GUARDAR CORTE----
@app.route("/guardar_corte", methods=["POST"])
@login_requerido
def guardar_corte():
    try:
        # Captura de datos con strip() para eliminar espacios
        fecha_str = request.form.get("fecha", "").strip()
        numero_corte = request.form.get("corte", "").strip()
        color_id = request.form.get("color", "").strip()
        metros = request.form.get("metros", "").strip()
        tallas_seleccionadas = request.form.getlist("tallas")
        cantidad_str = request.form.get("cantidad", "").strip()

        # 🔹 Validación de campos vacíos antes de convertir
        if not (fecha_str and numero_corte and color_id and metros and cantidad_str and tallas_seleccionadas):
            flash("⚠️ Todos los campos son obligatorios.", "danger")
            return redirect(url_for("cortes"))

        # Conversión segura a número
        try:
            cantidad = int(cantidad_str)
            metros = float(metros)
        except ValueError:
            flash("⚠️ Verifica los campos numéricos (cantidad o metros).", "danger")
            return redirect(url_for("cortes"))

        cantidad_corte = cantidad * len(tallas_seleccionadas)

        # 🔍 Validar duplicado
        corte_existente = Corte.query.filter_by(numero_corte=numero_corte).first()
        if corte_existente:
            flash(f"El número de corte {numero_corte} ya existe.", "warning")
            return redirect(url_for("cortes"))

        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        # Crear Corte
        corte = Corte(
            fecha=fecha,
            numero_corte=numero_corte,
            color_id=color_id,
            metros=metros,
            cantidad_corte=cantidad_corte,
            estado="Por_Coser"
        )
        db.session.add(corte)
        db.session.commit()

        # Obtener status "Cortada"
        status_cortada = Status.query.filter_by(nombre="Cortadas").first()
        if not status_cortada:
            flash("No existe el estado 'Cortadas' en la tabla Status.", "danger")
            return redirect(url_for("cortes"))

        # Crear producciones iniciales y registrar en historial
        for talla_id in tallas_seleccionadas:
            nueva_prod = Produccion(
                corte_id=corte.id,
                talla_id=talla_id,
                cantidad=cantidad,
                status_id=status_cortada.id,
                fecha_corte=corte.fecha
            )
            db.session.add(nueva_prod)

            # 🔹 Registrar también en HistorialProduccion
            talla = Talla.query.get(talla_id)
            color = Color.query.get(color_id)

            usuario_actual = session.get("usuario", "Sistema")

            historial = HistorialProduccion(
                corte_id=corte.id,
                historial_numero_corte=corte.numero_corte,
                historial_talla=talla.nombre,
                historial_color=color.nombre,
                historial_cantidad=cantidad,
                historial_status_id=status_cortada.id,
                usuario=usuario_actual,
                observacion="Registro inicial del corte"
            )
            db.session.add(historial)

        db.session.commit()
        flash("✅ Corte registrado con éxito", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Ocurrió un error al guardar el corte: {str(e)}", "danger")

    return redirect(url_for("cortes"))


# ---- RUTA PARA EDITAR CORTE ----
@app.route("/editar_corte/<int:corte_id>", methods=["GET", "POST"])
@login_requerido
def editar_corte(corte_id):
    corte = Corte.query.get_or_404(corte_id)
    colores = Color.query.all()
    tallas = Talla.query.all()
    produccion = Produccion.query.filter_by(corte_id=corte.id).all()

    if any(p.status.nombre != "Cortadas" for p in produccion):
        flash("❌ No se puede editar este corte porque una o más tallas ya avanzaron en producción.", "danger")
        return redirect(url_for("ver_cortes"))

    cantidad_existente = sum(p.cantidad for p in produccion if p.status.nombre != "Cortadas")

    if request.method == "POST":
        try:
            fecha_str = request.form["fecha"]
            nueva_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            numero_corte = request.form["corte"]
            color_id = int(request.form["color"])
            metros = float(request.form["metros"])
            tallas_seleccionadas = request.form.getlist("tallas")
            cantidad = int(request.form["cantidad"])
            cantidad_corte = cantidad * len(tallas_seleccionadas) + cantidad_existente

            status_eliminada = Status.query.filter_by(nombre="Ajuste_Baja").first()
            status_cortada = Status.query.filter_by(nombre="Cortadas").first()
            usuario_actual = session.get("usuario", "Sistema")

            # Validar duplicado de número de corte
            corte_existente = Corte.query.filter(
                Corte.numero_corte == numero_corte,
                Corte.id != corte.id
            ).first()
            if corte_existente:
                flash(f"El número de corte {numero_corte} ya existe en otro registro.", "warning")
                return redirect(url_for("editar_corte", corte_id=corte.id))

            # 🔹 Detectar cambios generales
            cambios = []
            if corte.fecha != nueva_fecha:
                cambios.append(f"Fecha: {corte.fecha} → {nueva_fecha}")
            if corte.numero_corte != numero_corte:
                cambios.append(f"Número de corte: {corte.numero_corte} → {numero_corte}")
            if corte.metros != metros:
                cambios.append(f"Metros: {corte.metros} → {metros}")
            if corte.color_id != color_id:
                color_anterior = Color.query.get(corte.color_id).nombre
                color_nuevo = Color.query.get(color_id).nombre
                cambios.append(f"Color: {color_anterior} → {color_nuevo}")

            # 🔹 Actualizar datos del corte
            corte.fecha = nueva_fecha
            corte.numero_corte = numero_corte
            corte.color_id = color_id
            corte.metros = metros
            corte.cantidad_corte = cantidad_corte

            # 🔹 Sincronizar fecha en Producción si cambia la fecha del corte
            for p in produccion:
                if p.fecha_corte != nueva_fecha:
                    p.fecha_corte = nueva_fecha

            # --- Producciones ---
            producciones_existentes = Produccion.query.filter_by(corte_id=corte.id).all()
            produccion_dict = {str(p.talla_id): p for p in producciones_existentes}
            color = Color.query.get(color_id)

            # 🔹 Registrar cambios o nuevas producciones
            for talla_id in tallas_seleccionadas:
                talla = Talla.query.get(talla_id)

                if talla_id in produccion_dict:
                    produccion_existente = produccion_dict[talla_id]
                    if produccion_existente.status_id == status_cortada.id:
                        if produccion_existente.cantidad != cantidad:
                            produccion_existente.cantidad = cantidad
                            historial = HistorialProduccion(
                                corte_id=corte.id,
                                historial_numero_corte=corte.numero_corte,
                                historial_talla=talla.nombre,
                                historial_color=color.nombre,
                                historial_cantidad=cantidad,
                                historial_status_id=status_cortada.id,
                                usuario=usuario_actual,
                                observacion="Edición de corte (Actualización de cantidad por talla)"
                            )
                            db.session.add(historial)

                else:
                    nueva_produccion = Produccion(
                        corte_id=corte.id,
                        talla_id=talla_id,
                        cantidad=cantidad,
                        status_id=status_cortada.id,
                        fecha_corte=corte.fecha
                    )
                    db.session.add(nueva_produccion)
                    historial = HistorialProduccion(
                        corte_id=corte.id,
                        historial_numero_corte=corte.numero_corte,
                        historial_talla=talla.nombre,
                        historial_color=color.nombre,
                        historial_cantidad=cantidad,
                        historial_status_id=status_cortada.id,
                        usuario=usuario_actual,
                        observacion="Edición de corte (Talla agregada al corte)"
                    )
                    db.session.add(historial)

            # 🔹 Eliminar tallas removidas
            for talla_id, produccion_existente in produccion_dict.items():
                if talla_id not in tallas_seleccionadas and produccion_existente.status_id == status_cortada.id:
                    talla = Talla.query.get(talla_id)
                    db.session.delete(produccion_existente)
                    historial = HistorialProduccion(
                        corte_id=corte.id,
                        historial_numero_corte=corte.numero_corte,
                        historial_talla=talla.nombre,
                        historial_color=corte.color.nombre,
                        historial_cantidad=produccion_existente.cantidad,
                        historial_status_id=status_eliminada.id,
                        usuario=usuario_actual,
                        observacion="Edición de corte (Talla eliminada del corte)"
                    )
                    db.session.add(historial)

            # 🔹 Si hubo cambios generales (fecha, color, metros, etc.)
            if cambios:
                detalle = "; ".join(cambios)
                for p in produccion:
                    talla = p.talla.nombre
                    historial_general = HistorialProduccion(
                        corte_id=corte.id,
                        historial_numero_corte=corte.numero_corte,
                        historial_talla=talla,
                        historial_color=corte.color.nombre,
                        historial_cantidad=p.cantidad,
                        historial_status_id=status_cortada.id,
                        usuario=usuario_actual,
                        observacion=f"Actualización de datos generales ({detalle})"
                    )
                    db.session.add(historial_general)

            db.session.commit()
            flash("✅ Corte actualizado correctamente y cambios registrados en historial.", "success")
            return redirect(url_for("editar_corte", corte_id=corte_id))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Ocurrió un error al actualizar el corte: {str(e)}", "danger")
            return redirect(url_for("editar_corte", corte_id=corte_id))

    if not produccion:
        flash("❌ No se puede editar el corte, no tiene producciones asociadas.", "danger")
        return redirect(url_for("ver_cortes"))

    produccion_dict = {str(p.talla_id): p for p in produccion}

    return render_template(
        "editar_corte.html",
        corte=corte,
        colores=colores,
        tallas=tallas,
        produccion=produccion,
        produccion_dict=produccion_dict
    )

# ---- RUTA PARA ELIMINAR CORTE ----
@app.route("/cortes/eliminar/<int:corte_id>")
@login_requerido
def eliminar_corte(corte_id):
    corte = Corte.query.get_or_404(corte_id)

    try:
        producciones = corte.producciones
        usuario_actual = session.get("usuario", "Sistema")
        status_eliminada = Status.query.filter_by(nombre="Ajuste_Baja").first()

        # 🚨 Evitar eliminar si alguna producción avanzó de estado
        if any(prod.status and prod.status.nombre != "Cortadas" for prod in producciones):
            flash(
                f"❌ No se puede eliminar el corte #{corte.numero_corte} porque tiene tallas en producción.",
                "danger"
            )
            return redirect(url_for("ver_cortes"))

        # 🔹 Registrar en historial ANTES de borrar
        for produccion in producciones:
            talla = Talla.query.get(produccion.talla_id)
            color = Color.query.get(corte.color_id)

            historial = HistorialProduccion(
                corte_id=corte.id,  # se conserva por trazabilidad (aunque no haya FK real)
                historial_numero_corte=corte.numero_corte,
                historial_talla=talla.nombre if talla else "N/A",
                historial_color=color.nombre if color else "N/A",
                historial_cantidad=produccion.cantidad,
                historial_status_id=status_eliminada.id if status_eliminada else produccion.status_id,
                fecha_status=fecha_local_tijuana(),
                usuario=usuario_actual,
                observacion=f"Corte #{corte.numero_corte} eliminado por {usuario_actual}"
            )
            db.session.add(historial)

            # 🔁 Actualizar estatus a "Ajuste_Baja"
            if status_eliminada:
                produccion.status_id = status_eliminada.id

        # 💾 Guardar historial ANTES de borrar
        db.session.commit()

        # ✅ Eliminar producciones y corte
        for produccion in producciones:
            db.session.delete(produccion)

        db.session.delete(corte)
        db.session.commit()

        flash(f"✅ Corte #{corte.numero_corte} eliminado correctamente y registrado en historial", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al eliminar corte: {str(e)}", "danger")

    return redirect(url_for("ver_cortes"))


#----RUTA PARA LISTAR CORTES----
@app.route("/cortes_listado")
@login_requerido
def ver_cortes():

    # Carga datos para selects
    colores = Color.query.order_by(Color.nombre).all()
    tallas = Talla.query.order_by(Talla.id).all()
    estados = Status.query.order_by(Status.id).all()
    #estados = Status.query.filter(Status.fase == "Producción").order_by(Status.id).all()


    # Base query de cortes
    q = Corte.query

    # Filtros simples sobre Corte
    numero_corte = request.args.get("numero_corte", "").strip()
    fecha_filtro = request.args.get("fecha", "").strip()
    color_id = request.args.get('color_id', type=int)

    if numero_corte:
        try:
            numero_corte_int = int(numero_corte)
            q = q.filter(Corte.numero_corte == numero_corte_int)
        except ValueError:
            flash("El número de corte debe ser un valor numérico", "warning")

    if fecha_filtro:
        try:
            fecha_dt = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
            q = q.filter(Corte.fecha == fecha_dt)
        except ValueError:
            flash("Formato de fecha inválido. Usa AAAA-MM-DD.", "warning")

    if color_id:
        q = q.filter(Corte.color_id == color_id)

    # Filtros que dependen de Producción (join necesario)

    talla_id = request.args.get('talla_id', type=int)
    estado_id = request.args.get('estado', type=int)

    if color_id or talla_id or estado_id:
        q = q.join(Corte.producciones)  # relación Corte -> Producciones
        if talla_id:
            q = q.filter(Produccion.talla_id == talla_id)
        if estado_id:
            q = q.filter(Produccion.status_id == estado_id)

    # Evitar cortes duplicados por join
    cortes = q.distinct().all()

    return render_template(
        "cortes_listado.html",
        colores=colores,
        tallas=tallas,
        estados=estados,
        cortes=cortes,
    )

#----RUTA PARA LISTAR PRODUCCIÓN----
@app.route("/produccion", methods=["GET", "POST"])
@login_requerido
def produccion_listado():

    # Carga filtros y listas para selects
    colores = Color.query.order_by(Color.nombre).all()
    tallas = Talla.query.order_by(Talla.id).all()
    estados = Status.query.order_by(Status.id).all()

    q = Produccion.query.join(Status).join(Color).join(Talla)

    color_id = request.args.get('color_id', type=int)
    talla_id = request.args.get('talla_id', type=int)
    estado_id = request.args.get('estado', type=int)
    numero_corte = request.args.get("numero_corte", "").strip()
    fecha_filtro = request.args.get("fecha", "").strip()

    if color_id:
        q = q.filter(Produccion.color_id == color_id)
    if talla_id:
        q = q.filter(Produccion.talla_id == talla_id)
    if estado_id:
        q = q.filter(Produccion.status_id == estado_id)

    if numero_corte:
        try:
            numero_corte_int = int(numero_corte)
            q = q.join(Corte, Produccion.corte_id == Corte.id) \
                 .filter(Corte.numero_corte == numero_corte_int)
        except ValueError:
            flash("El número de corte debe ser un valor numérico", "warning")

    if fecha_filtro:
        try:
            fecha_dt = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
            q = q.join(Corte, Produccion.corte_id == Corte.id) \
                 .filter(Corte.fecha == fecha_dt)
        except ValueError:
            flash("Formato de fecha inválido. Usa AAAA-MM-DD.", "warning")

    producciones = q.order_by(Produccion.corte_id, Produccion.talla_id).all()

    cortes_grouped = []
    by_corte = {}
    for p in producciones:
        c_id = p.corte_id or 0
        if c_id not in by_corte:
            by_corte[c_id] = {
                "corte": p.corte if p.corte else None,
                "color_nombre": p.color.nombre,
                "producciones": [],
                "total_in_view": 0
            }
        by_corte[c_id]["producciones"].append(p)
        by_corte[c_id]["total_in_view"] += p.cantidad

    for k, v in by_corte.items():
        cortes_grouped.append(v)

    return render_template("produccion.html",
                           cortes_grouped=cortes_grouped,
                           colores=colores,
                           tallas=tallas,
                           estados=estados)


# --- RUTA PARA VISTA RÁPIDA DE COSTURA (solo fases de producción) ---
@app.route("/actualizar_estados", methods=["GET"])
@login_requerido
def actualizar_estados():
    # Carga de listas para selects
    colores = Color.query.order_by(Color.nombre).all()
    tallas = Talla.query.order_by(Talla.id).all()
    estados = Status.query.filter(Status.fase == "Producción").order_by(Status.id).all()

    # 🔹 Filtrar SOLO los estados de producción
    estados_produccion = ["Cortadas", "Cosidas", "Dobladas"]
    estados_ids = [s.id for s in Status.query.filter(Status.nombre.in_(estados_produccion)).all()]

    # 🔹 Query base: Producción con joins necesarios
    q = (
        Produccion.query
        .join(Status)
        .join(Talla)
        .join(Corte)      # 👈 relación con Corte
        .join(Color)      # 👈 relación indirecta para obtener color
        .filter(Produccion.status_id.in_(estados_ids))
    )

    # --- Aplicar filtros GET ---
    color_id = request.args.get('color_id', type=int)
    talla_id = request.args.get('talla_id', type=int)
    estado_id = request.args.get('estado', type=int)
    numero_corte = request.args.get("numero_corte", "").strip()
    fecha_filtro = request.args.get("fecha", "").strip()

    if color_id:
        q = q.filter(Corte.color_id == color_id)  # ✅ Ahora el color viene desde Corte
    if talla_id:
        q = q.filter(Produccion.talla_id == talla_id)
    if estado_id:
        q = q.filter(Produccion.status_id == estado_id)
    if numero_corte:
        try:
            numero_corte_int = int(numero_corte)
            q = q.filter(Corte.numero_corte == numero_corte_int)
        except ValueError:
            flash("El número de corte debe ser un valor numérico", "warning")
    if fecha_filtro:
        try:
            fecha_dt = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
            q = q.filter(Corte.fecha == fecha_dt)
        except ValueError:
            flash("Formato de fecha inválido. Usa AAAA-MM-DD.", "warning")

    # --- Ordenar y agrupar por corte ---
    producciones = q.order_by(Produccion.corte_id, Produccion.talla_id).all()

    cortes_grouped = []
    by_corte = {}
    for p in producciones:
        c_id = p.corte_id or 0
        if c_id not in by_corte:
            by_corte[c_id] = {
                "corte": p.corte if p.corte else None,
                "color_nombre": p.corte.color.nombre if p.corte and p.corte.color else "Sin color",
                "producciones": [],
                "total_in_view": 0
            }
        by_corte[c_id]["producciones"].append(p)
        by_corte[c_id]["total_in_view"] += p.cantidad

    for k, v in by_corte.items():
        cortes_grouped.append(v)

    return render_template(
        "actualizar_estados.html",
        cortes_grouped=cortes_grouped,
        colores=colores,
        tallas=tallas,
        estados=estados
    )


#----RUTA PARA MARCAR ESTADO DE COSTURA EN MASA----
@app.route("/marcar_estado_costura", methods=["POST"])
@login_requerido
def marcar_estado_costura():
    try:
        ids = request.form.getlist("produccion_ids")
        target_status_id = int(request.form.get("target_status_id"))

        if not ids:
            flash("No seleccionaste ninguna producción.", "warning")
            return redirect(url_for("actualizar_estados"))

        # Validar estado destino
        status = Status.query.get(target_status_id)
        if not status:
            flash("Estado destino inválido.", "danger")
            return redirect(url_for("actualizar_estados"))

        updated = 0
        for pid in ids:
            p = Produccion.query.get(int(pid))
            if p:
                # 🔹 1) Actualizar el estado en Produccion
                p.status_id = target_status_id
                updated += 1

                # 🔹 2) Crear registro en el historial de producción
                usuario_actual = session.get("usuario", "Sistema")

                historial = HistorialProduccion(
                    corte_id=p.corte_id,
                    historial_numero_corte=p.corte.numero_corte,
                    historial_talla=p.talla.nombre,
                    historial_color=p.color.nombre,
                    historial_cantidad=p.cantidad,
                    historial_status_id=target_status_id,
                    usuario=usuario_actual,  # ← aquí podrías usar session["usuario"] si tienes login
                    observacion=f"Actualizado a '{status.nombre}' desde vista rápida"
                )
                db.session.add(historial)

        # 🔹 3) Confirmar todos los cambios
        db.session.commit()
        flash(f"{updated} registro(s) actualizados y guardados en historial.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Ocurrió un error al actualizar: {str(e)}", "danger")

    return redirect(url_for("actualizar_estados"))


# --- RUTA PARA VER EL HISTORIAL DEL ESTATUS ---
@app.route("/historial_status", methods=["GET"])
@login_requerido
def historial_status():
    colores = Color.query.order_by(Color.nombre).all()
    estados = Status.query.order_by(Status.nombre).all()
    tallas_existentes = Talla.query.order_by(Talla.id).all()
    tallas = [t.nombre for t in tallas_existentes]

    # Base query
    q = HistorialProduccion.query.outerjoin(Status)

    # Filtros
    numero_corte = request.args.get("numero_corte", "").strip()
    color_id = request.args.get("color_id", "").strip()
    talla_id = request.args.get("talla_id", "").strip()
    estado_id = request.args.get("estado", type=int)
    fecha_inicio = request.args.get("fecha_inicio", "").strip()
    fecha_fin = request.args.get("fecha_fin", "").strip()
    solo_actuales = request.args.get("solo_actuales") == "1"

    # 🔹 Filtro por número de corte
    if numero_corte:
        try:
            num = int(numero_corte)
            q = q.filter(HistorialProduccion.historial_numero_corte == num)
        except ValueError:
            flash("⚠️ El número de corte debe ser numérico.", "warning")

    # 🔹 Filtro por color
    if color_id:
        color = Color.query.get(int(color_id))
        if color:
            q = q.filter(HistorialProduccion.historial_color == color.nombre)

    # 🔹 Filtro por talla
    if talla_id:
        talla = Talla.query.get(int(talla_id))
        if talla:
            q = q.filter(HistorialProduccion.historial_talla == talla.nombre)

    # 🔹 Filtro por estado
    if estado_id:
        q = q.filter(HistorialProduccion.historial_status_id == estado_id)

    # 🔹 Filtro por fechas
    if fecha_inicio:
        try:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            q = q.filter(HistorialProduccion.fecha_status >= fi)
        except:
            flash("Formato de fecha de inicio inválido.", "warning")

    if fecha_fin:
        try:
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
            q = q.filter(HistorialProduccion.fecha_status < ff)
        except:
            flash("Formato de fecha de fin inválido.", "warning")

    # 🔹 Obtener registros
    historial = q.order_by(HistorialProduccion.fecha_status.desc()).all()

    # 🔹 Mostrar solo los más recientes por talla (si el checkbox está activo)
    if solo_actuales:
        vistos = {}
        filtrados = []
        for h in historial:
            clave = (h.historial_numero_corte, h.historial_talla)
            if clave not in vistos:
                vistos[clave] = True
                filtrados.append(h)
        historial = filtrados

    return render_template(
        "historial_status.html",
        historial=historial,
        colores=colores,
        estados=estados,
        tallas=tallas,
        tallas_existentes=tallas_existentes,
        solo_actuales=solo_actuales
    )


# ---- RUTA PARA DASHBOARD DE PRODUCCIÓN ----

@app.route("/dashboard_produccion", methods=["GET"])
@login_requerido
def dashboard_produccion():
    mes = request.args.get("mes")
    anio = request.args.get("anio")

    filtro_cortes = []
    filtro_produccion = []

    if mes and anio:
        filtro_cortes += [extract("month", Corte.fecha) == int(mes), extract("year", Corte.fecha) == int(anio)]
        filtro_produccion += [extract("month", Corte.fecha) == int(mes), extract("year", Corte.fecha) == int(anio)]
    elif anio:
        filtro_cortes.append(extract("year", Corte.fecha) == int(anio))
        filtro_produccion.append(extract("year", Corte.fecha) == int(anio))

    total_cortes = Corte.query.filter(*filtro_cortes).count() if filtro_cortes else Corte.query.count()
    total_playeras = (
        db.session.query(func.sum(Produccion.cantidad))
        .join(Corte, Produccion.corte_id == Corte.id)
        .filter(*filtro_produccion)
        .scalar()
        or 0
    )

    color_mas_producido = (
        db.session.query(Color.nombre, func.sum(Produccion.cantidad).label("total"))
        .join(Corte, Produccion.corte_id == Corte.id)
        .join(Color, Corte.color_id == Color.id)
        .filter(*filtro_produccion)
        .group_by(Color.nombre)
        .order_by(desc("total"))
        .first()
    )
    color_nombre = color_mas_producido[0] if color_mas_producido else "N/A"
    color_total = color_mas_producido[1] if color_mas_producido else 0

    talla_mas_producida = (
        db.session.query(Talla.nombre, func.sum(Produccion.cantidad).label("total"))
        .join(Talla, Produccion.talla_id == Talla.id)
        .join(Corte, Produccion.corte_id == Corte.id)
        .filter(*filtro_produccion)
        .group_by(Talla.nombre)
        .order_by(desc("total"))
        .first()
    )
    talla_nombre = talla_mas_producida[0] if talla_mas_producida else "N/A"
    talla_total = talla_mas_producida[1] if talla_mas_producida else 0

    total_metros = (
        db.session.query(func.sum(Corte.metros))
        .filter(*filtro_cortes)
        .scalar()
        or 0
    )

    produccion_por_color = (
        db.session.query(Color.nombre, func.sum(Produccion.cantidad).label("total"))
        .join(Corte, Produccion.corte_id == Corte.id)
        .join(Color, Corte.color_id == Color.id)
        .filter(*filtro_produccion)
        .group_by(Color.nombre)
        .order_by(Color.nombre)
        .all()
    )

    colores_labels = [r[0] for r in produccion_por_color]
    colores_totales = [r[1] for r in produccion_por_color]

    produccion_por_talla = (
        db.session.query(Talla.nombre, func.sum(Produccion.cantidad).label("total"))
        .join(Talla, Produccion.talla_id == Talla.id)
        .join(Corte, Produccion.corte_id == Corte.id)
        .filter(*filtro_produccion)
        .group_by(Talla.nombre)
        .order_by(Talla.nombre)
        .all()
    )

    tallas_labels = [r[0] for r in produccion_por_talla]
    tallas_totales = [r[1] for r in produccion_por_talla]

    años_disponibles = [
        r[0] for r in db.session.query(extract("year", Corte.fecha)).distinct().all()
    ]

    # ✅ Agregamos datetime para usar now() en Jinja
    return render_template(
        "dashboard_produccion.html",
        total_cortes=total_cortes,
        total_playeras=total_playeras,
        color_nombre=color_nombre,
        color_total=color_total,
        talla_nombre=talla_nombre,
        talla_total=talla_total,
        total_metros=total_metros,
        años_disponibles=años_disponibles,
        mes=mes,
        anio=anio,
        colores_labels=colores_labels,
        colores_totales=colores_totales,
        tallas_labels=tallas_labels,
        tallas_totales=tallas_totales,
        now=datetime.now  # 👈 Esto habilita el uso de now() en el template
    )


# 🔹 NUEVA RUTA: API para resumen mensual
@app.route("/api/resumen_mes")
def api_resumen_mes():
    mes_str = request.args.get("mes")  # formato: "2025-10"
    if not mes_str:
        hoy = date.today()
        mes_str = f"{hoy.year}-{hoy.month:02d}"

    anio, mes = map(int, mes_str.split("-"))

    resultados = (
        db.session.query(Corte.fecha, func.sum(Produccion.cantidad).label("total"))
        .join(Corte)
        .filter(extract("year", Corte.fecha) == anio)
        .filter(extract("month", Corte.fecha) == mes)
        .group_by(Corte.fecha)
        .order_by(Corte.fecha)
        .all()
    )

    data = [{"fecha": r.fecha.strftime("%Y-%m-%d"), "total": int(r.total)} for r in resultados]
    return jsonify(data)


# ==========================
#   RUTA: Recepción de Producción
# ==========================

@app.route('/recepcion_produccion')
@login_requerido
def recepcion_produccion():

    # Obtener el ID del status "Enviada_a_inventario"
    status_envio = Status.query.filter_by(nombre="Enviadas_a_Inventario").first()
    prendas_enviadas = Produccion.query.filter_by(status_id=status_envio.id).all()

    return render_template('recepcion_produccion.html', prendas=prendas_enviadas)

@app.route('/recepcionar/<int:id>', methods=['POST'])
def recepcionar_prenda(id):
    prenda = Produccion.query.get_or_404(id)

    status_inventario = Status.query.filter_by(nombre="En_Inventario").first()

    # 🔹 Actualizar status de producción
    prenda.status_id = status_inventario.id

    # 🔹 Registrar o actualizar inventario
    inventario = Inventario.query.filter_by(color_id=prenda.corte.color.id, talla_id=prenda.talla.id).first()
    usuario_actual = session.get("usuario", "Sistema")

    if inventario:
        inventario.cantidad += prenda.cantidad
    else:
        try:                                    
            inventario = Inventario(
                color_id=prenda.corte.color.id,
                talla_id=prenda.talla.id,
                cantidad=prenda.cantidad,
                status_id=status_inventario.id,
                usuario = usuario_actual,
                observaciones = "Ingreso inicial al inventario desde recepción de producción"
            )
            db.session.add(inventario)
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Ocurrió un error al crear el inventario: {str(e)}", "danger")
            return redirect(url_for('recepcion_produccion'))

    # 🔹 Registrar en historial
    historial = HistorialInventario(
        inventario=inventario,
        tipo_movimiento="Recepción Producción",
        cantidad_historial=prenda.cantidad,
        fecha_movimiento=datetime.utcnow(),
        status_id=status_inventario.id,
        usuario = usuario_actual,
        observaciones = "Ingreso inicial al inventario desde recepción de producción"
    )
    db.session.add(historial)

    db.session.commit()


    flash(f"✅ Prenda '{prenda.color} T{prenda.talla}' recepcionada correctamente.", "success")
    return redirect(url_for('recepcion_produccion'))


# ==========================
#   RUTA: INGRESO MANUAL
# ==========================

@app.route("/ingreso_manual", methods=["GET", "POST"])
@login_requerido
def ingreso_manual():
    colores = Color.query.all()
    tallas = Talla.query.all()
    # Fecha de hoy según Tijuana
    fecha_hoy = datetime.now(ZoneInfo("America/Tijuana")).strftime("%Y-%m-%d")
    usuario_actual = session.get("usuario", "Sistema")

    if request.method == "POST":
        try:
            # Datos del formulario
            fecha = request.form.get("fecha")
            color_id = request.form.get("color")
            tallas_seleccionadas = request.form.getlist("tallas")
            cantidad = int(request.form.get("cantidad", 0))
            observaciones = request.form.get("observaciones", "").strip()

            # Validaciones básicas
            if not color_id or not tallas_seleccionadas or cantidad <= 0:
                flash("⚠️ Debes seleccionar un color, al menos una talla y una cantidad válida.", "warning")
                return redirect(url_for("ingreso_manual"))

            # Obtener el estado 'En_Inventario'
            status_inventario = Status.query.filter_by(nombre="En_Inventario").first()
            if not status_inventario:
                flash("❌ No se encontró el estado 'En_Inventario' en la tabla Status.", "danger")
                return redirect(url_for("ingreso_manual"))
            
            # Hora exacta de Tijuana ⏰
            ahora_tijuana = datetime.now(ZoneInfo("America/Tijuana"))

            # Registrar por cada talla seleccionada
            for talla_id in tallas_seleccionadas:
                talla_id = int(talla_id)

                # Verificar si ya existe un registro con ese color y talla
                registro_existente = Inventario.query.filter_by(
                    color_id=color_id,
                    talla_id=talla_id,
                    status_id=status_inventario.id
                ).first()

                if registro_existente:
                    # Si existe, sumar cantidad
                    registro_existente.cantidad += cantidad
                    registro_existente.observaciones = (
                        (registro_existente.observaciones or "") +
                        f"\nIngreso manual {ahora_tijuana.strftime('%Y-%m-%d %H:%M')} - +{cantidad}"
                    )
                else:
                    # Crear nuevo registro
                    nuevo_registro = Inventario(
                        color_id=color_id,
                        talla_id=talla_id,
                        cantidad=cantidad,
                        status_id=status_inventario.id,
                        usuario=usuario_actual,  # Cambia por current_user.username si usas Flask-Login
                        observaciones=observaciones,
                        fecha=datetime.strptime(fecha, "%Y-%m-%d")
                    )
                    db.session.add(nuevo_registro)
                    db.session.flush()  # Para obtener el ID antes del commit

                    registro_existente = nuevo_registro

                # Crear movimiento en historial
                movimiento = HistorialInventario(
                    inventario_id=registro_existente.id,
                    tipo_movimiento="Ingreso Manual",
                    cantidad_historial=cantidad,
                    status_id=status_inventario.id,
                    fecha_movimiento=ahora_tijuana,  # ⏰ hora precisa
                    usuario=usuario_actual,  # idem
                    observaciones=f"Ingreso manual el {fecha} - Cantidad: {cantidad}"
                )
                db.session.add(movimiento)

            db.session.commit()
            flash("✅ Ingreso manual registrado correctamente en el inventario.", "success")
            return redirect(url_for("inventario_disponible"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al registrar ingreso manual: {str(e)}", "danger")

    return render_template("ingreso_manual.html", colores=colores, tallas=tallas, fecha_hoy=fecha_hoy)


# ===============================
#   RUTA: Inventario solo Estatus "En_Inventario"
# ===============================
@app.route("/inventario_disponible", methods=["GET"])
@login_requerido
def inventario_disponible():
    color_id = request.args.get("color_id")
    talla_id = request.args.get("talla_id")

    colores = Color.query.all()
    tallas = Talla.query.all()
    estados = Status.query.all()

    # Consulta base de inventario
    inventarios = db.session.query(Inventario).join(Color).join(Talla).join(Status)
    inventarios = inventarios.order_by(Talla.id.asc())
    inventarios = inventarios.filter(Inventario.status_id == 5, Inventario.cantidad > 0) #Estatus de "En_Inventario" y Cantidad mayor a "0"

    # Aplicar filtros
    if color_id and color_id != "":
        inventarios = inventarios.filter(Inventario.color_id == color_id)
    if talla_id and talla_id != "":
        inventarios = inventarios.filter(Inventario.talla_id == talla_id)

    inventarios = inventarios.all()

    # 🔥 FILTRAR: solo colores que tengan tallas en inventario
    colores_con_inventario = {inv.color_id for inv in inventarios}
    colores = [c for c in colores if c.id in colores_con_inventario]

    return render_template(
        "inventario_disponible.html",
        colores=colores,
        tallas=tallas,
        estados=estados,
        inventarios=inventarios,
        color_seleccionado=color_id,
        talla_seleccionada=talla_id
    )

# ===============================
#   RUTA: Inventario General
# ===============================
@app.route("/inventario_general", methods=["GET"])
@login_requerido
def inventario_general():
    color_id = request.args.get("color_id")
    talla_id = request.args.get("talla_id")
    estado_id = request.args.get("estado")

    colores = Color.query.all()
    tallas = Talla.query.all()
    estados = Status.query.filter(Status.fase == "Inventario").order_by(Status.id).all()

    # Consulta base de inventario
    inventarios = db.session.query(Inventario).join(Color).join(Talla).join(Status)
    inventarios = inventarios.order_by(Talla.id.asc())
    inventarios = inventarios.filter(Inventario.cantidad > 0)

    # Aplicar filtros
    if color_id and color_id != "":
        inventarios = inventarios.filter(Inventario.color_id == color_id)
    if talla_id and talla_id != "":
        inventarios = inventarios.filter(Inventario.talla_id == talla_id)
    if estado_id and estado_id != "":
        inventarios = inventarios.filter(Inventario.status_id == estado_id)

    inventarios = inventarios.all()

    # 🔥 FILTRAR: solo colores que tengan tallas en inventario
    colores_con_inventario = {inv.color_id for inv in inventarios}
    colores = [c for c in colores if c.id in colores_con_inventario]

    return render_template(
        "inventario_general.html",
        colores=colores,
        tallas=tallas,
        estados=estados,
        inventarios=inventarios,
        color_seleccionado=color_id,
        talla_seleccionada=talla_id,
        estado_seleccionado=estado_id,
    )

# ===============================
#   RUTA: Editar Inventario (POST)
# ===============================
@app.route("/editar_inventario/<int:id>", methods=["POST"])
def editar_inventario(id):
    inventario = Inventario.query.get_or_404(id)
    usuario_actual = session.get("usuario", "Sistema")

    cantidad_actual = inventario.cantidad
    nueva_cantidad = int(request.form.get("cantidad", cantidad_actual))

    diferencia = nueva_cantidad - cantidad_actual

    status_inventario = Status.query.filter_by(nombre="En_Inventario").first()
    status_eliminada = Status.query.filter_by(nombre="Ajuste_Baja").first()

    if not status_inventario or not status_eliminada:
        flash("Error: No se encontraron los estados requeridos ('En_Inventario' o 'Ajuste_Baja').", "danger")
        return redirect(url_for("inventario_disponible"))

    # === CASO 1: Cantidad disminuyó ===
    if diferencia < 0:
        cantidad_eliminada = abs(diferencia)

        # 1️ Actualizar el registro original con la cantidad restante
        inventario.cantidad = nueva_cantidad
        db.session.add(inventario)

        # 2️ Verificar si ya existe un registro con ese color y talla en estado "Eliminada"
        registro_existente = Inventario.query.filter_by(
            color_id=inventario.color_id,
            talla_id=inventario.talla_id,
            status_id=status_eliminada.id
        ).first()

        # 3️ Si existe, sumar cantidad; si no, crear nuevo registro
        if registro_existente:
            # Si existe, sumar cantidad
            registro_existente.cantidad += cantidad_eliminada
            registro_existente.observaciones = (
                (registro_existente.observaciones or "") +
                f"\nMovimiento desde edición de inventario ID {inventario.id} - +{cantidad_eliminada}"
            )
            db.session.add(registro_existente)
        else:
            #  Si no existe, crear un nuevo registro para la cantidad eliminada con estatus 'Eliminada'
            inventario_eliminada = Inventario(
                color_id=inventario.color_id,
                talla_id=inventario.talla_id,
                cantidad=cantidad_eliminada,
                status_id=status_eliminada.id,
                usuario=usuario_actual,
                fecha=datetime.utcnow(),
                observaciones=f"Prendas eliminadas desde edición de inventario ID {inventario.id}"
            )
            db.session.add(inventario_eliminada)
            db.session.flush()  # Para obtener el ID antes del commit

        # 4️ Registrar en historial el movimiento de eliminación
        movimiento = HistorialInventario(
            inventario_id=inventario.id,
            tipo_movimiento="Ajuste Baja",
            cantidad_historial=-cantidad_eliminada,
            status_id=status_eliminada.id,
            fecha_movimiento=datetime.utcnow(),
            usuario=usuario_actual,
            observaciones=f"Se eliminaron {cantidad_eliminada} playeras por ajuste de inventario ID {inventario.id}"
        )
        db.session.add(movimiento)

        # 5 Registrar en HistorialSalidas
        salida = HistorialSalidas(
            inventario_id=inventario.id,
            status_salida_id=status_eliminada.id,
            cantidad=cantidad_eliminada,
            tipo_salida="Ajuste Baja",
            observaciones=f"Se generó nuevo registro de inventario con {cantidad_eliminada} unidades eliminadas.",
            usuario=usuario_actual,
            fecha_salida=datetime.utcnow()
        )
        db.session.add(salida)
        flash(f"Se movieron {cantidad_eliminada} prendas a estatus 'Ajuste_Baja' por ajuste en el inventario.", "warning")

    # === CASO 2: Cantidad aumentó ===
    elif diferencia > 0:
        inventario.cantidad = nueva_cantidad

        # Registrar en historial el movimiento de ingreso
        movimiento = HistorialInventario(
            inventario_id=inventario.id,
            tipo_movimiento="Ajuste Alta",
            cantidad_historial=diferencia,
            status_id=status_inventario.id,
            fecha_movimiento=datetime.utcnow(),
            usuario=usuario_actual,
            observaciones=f"Se agregaron {diferencia} prendas desde edición de inventario ID {inventario.id}"
        )
        db.session.add(movimiento)


        flash(f"Se agregaron {diferencia} prendas al inventario.", "success")


    db.session.commit()
    return redirect(url_for("inventario_disponible"))

# ===============================
#   RUTA: Salidas simples de inventario
# ===============================

@app.route("/salida_simple/<int:id>", methods=["POST"])
def salida_simple(id):
    tipo_salida = request.form["tipo_salida"]
    cantidad_salida = int(request.form["cantidad"])
    observacion = request.form.get("observacion", "")
    usuario_actual = session.get("usuario", "Sistema")

    inventario = Inventario.query.get_or_404(id)

    # Evitar cantidades negativas
    if inventario.cantidad < cantidad_salida:
        flash("Cantidad insuficiente en inventario", "danger")
        return redirect(url_for("inventario_disponible"))
    
    # Actualizar inventario
    inventario.cantidad -= cantidad_salida
    db.session.add(inventario)

    # Buscar Status correspondiente (por ejemplo: 'Dañada')
    status = Status.query.filter_by(nombre=tipo_salida).first()

    # Verificar si ya existe un registro con ese color y talla en estado "tipo" de "Salida"
    registro_existente = Inventario.query.filter_by(
        color_id=inventario.color_id,
        talla_id=inventario.talla_id,
        status_id=status.id
    ).first()

    # Si existe, sumar cantidad; si no, crear nuevo registro
    if registro_existente:
        # Si existe, sumar cantidad
        registro_existente.cantidad += cantidad_salida
        registro_existente.observaciones = (
            (registro_existente.observaciones or "") +
            f"\nMovimiento desde salida simple ID {inventario.id} - +{cantidad_salida}"
        )
        db.session.add(registro_existente)

    else:
        #  Si no existe, crear un nuevo registro para la cantidad con el estatus de "Salida" correspondiente
        inventario_salida = Inventario(
            color_id=inventario.color_id,
            talla_id=inventario.talla_id,
            cantidad=cantidad_salida,
            status_id=status.id,
            usuario=usuario_actual,
            fecha=datetime.utcnow(),
            observaciones=f"Prendas movidas desde salida simple ID {inventario.id} - Tipo: {tipo_salida}"
        )
        db.session.add(inventario_salida)
        db.session.flush()  # Para obtener el ID antes del commit

    # Registrar movimiento en historial
    movimiento = HistorialInventario(
        inventario_id=inventario.id,
        tipo_movimiento="Salidas",
        cantidad_historial=-cantidad_salida,
        status_id=status.id,
        fecha_movimiento=datetime.utcnow(),
        usuario=usuario_actual,
        observaciones=observacion
    )
    db.session.add(movimiento)
    # Registrar en HistorialSalidas
    salida = HistorialSalidas(
        inventario_id=inventario.id,
        status_salida_id=status.id,
        cantidad=cantidad_salida,
        tipo_salida=tipo_salida,
        observaciones=observacion,
        usuario=usuario_actual,
        fecha_salida=datetime.utcnow()
    )
    db.session.add(salida)

    db.session.commit()
    flash(f"Salida registrada ({tipo_salida}): {cantidad_salida} unidades", "success")

    return redirect(url_for("inventario_disponible"))


# ===============================
#   RUTA: Ver Historial de Inventario
# ===============================
@app.route("/ver_historial_inventario")
@login_requerido
def ver_historial_inventario():

    # Obtener filtros
    color_id = request.args.get("color_id", "")
    talla_id = request.args.get("talla_id", "")
    estado_id = request.args.get("estado", "")
    page = request.args.get("page", 1, type=int)
    per_page = 50  # 👉 Número de filas por página (ajústalo si quieres)

    # Catálogos
    colores = Color.query.all()
    tallas = Talla.query.all()
    estados = Status.query.filter(Status.fase == "Inventario").order_by(Status.id).all()

    # Consulta base
    movimientos = (
        db.session.query(HistorialInventario)
        .join(Inventario)
        .join(Status)
    )

    # Aplicar filtros
    if color_id:
        movimientos = movimientos.filter(Inventario.color_id == int(color_id))

    if talla_id:
        movimientos = movimientos.filter(Inventario.talla_id == int(talla_id))

    if estado_id:
        movimientos = movimientos.filter(HistorialInventario.status_id == int(estado_id))

    # Paginación
    movimientos = movimientos.order_by(
        HistorialInventario.fecha_movimiento.desc()
    ).paginate(page=page, per_page=per_page)

    return render_template(
        "ver_historial_inventario.html",
        movimientos=movimientos,
        colores=colores,
        tallas=tallas,
        estados=estados,
        color_seleccionado=color_id,
        talla_seleccionada=talla_id,
        estado_seleccionado=estado_id
    )

# --- RUTA PARA DAR SALIDAS POR LOTE---
@app.route("/surtido", methods=["GET","POST"])
@login_requerido
def surtido():
    colores = Color.query.order_by(Color.id).all()
    tallas = Talla.query.order_by(Talla.id).all()
    usuario_actual = session.get("usuario", "Sistema")

    # Obtener último pedido
    ultimo = Pedido.query.order_by(Pedido.id.desc()).first()

    # Si no existen pedidos, iniciamos desde 1
    if ultimo:
        try:
            ultimo_pedido = int(ultimo.numero_pedido) + 1
        except ValueError:
            # Si por alguna razón el numero_pedido es texto o no convertible, iniciamos desde 1
            ultimo_pedido = 1
    else:
        ultimo_pedido = 1


    return render_template("surtido.html", colores=colores, tallas=tallas, usuario_actual=usuario_actual, ultimo_pedido=ultimo_pedido)


@app.route("/obtener_siguiente_pedido")
def obtener_siguiente_pedido():
    ultimo = Pedido.query.order_by(Pedido.numero_pedido.desc()).first()
    siguiente = (ultimo.numero_pedido + 1) if ultimo else 1
    return jsonify({"siguiente_pedido": siguiente})

@app.route("/inventario_por_color/<int:color_id>")
def inventario_por_color(color_id):
    color = Color.query.get(color_id)
    tallas = Talla.query.order_by(Talla.id).all()
    inventarios = Inventario.query.filter_by(color_id=color_id, status_id=5).all()

    if not color:
        return jsonify({"error": "Color no encontrado"}), 404

    inventario_por_talla = {t.id: 0 for t in tallas}
    for inv in inventarios:
        inventario_por_talla[inv.talla_id] += inv.cantidad

    return jsonify({"color_id": color_id, "color_nombre": color.nombre, "tallas": [{"id": t.id, "nombre": t.nombre, "cantidad": inventario_por_talla[t.id], "costo": t.costo}
            for t in tallas
        ]
    })

# ===============================
# RUTA: Salida por lote
# ===============================
@app.route('/salida_lote', methods=['POST'])
def salida_lote():
    tallas=Talla.query.order_by(Talla.id).all()

    data = request.get_json()  # el JSON completo del pedido
    if not data:
        return jsonify({"status": "error", "mensaje": "No se recibieron datos"}), 400

    cliente = data.get("cliente")
    numero_pedido = data.get("pedido_numero")
    observaciones = data.get("observaciones", "")
    usuario_actual = session.get("usuario", "Sistema")
    detalles = data.get("detalles", [])
    errores = []
    costo_total = float(0)

    status_pedido= StatusPedido.query.filter_by(nombre="Surtido").first()
    estatus_en_inventario = Status.query.filter_by(nombre="En_Inventario").first()
    status_destino = Status.query.filter_by(nombre="Surtidas").first()

    # Calcular costo total
    for d in detalles:  # Cada detalle
        for talla in tallas: # Cada talla
            if d["talla_id"] == talla.id: # Si la talla coincide
                costo_total += talla.costo * d["cantidad"] # Multiplicar costo unitario por cantidad y sumar al costo total
                break

    # ===========================================
    # 🆕 Crear primero el pedido (encabezado)
    # ===========================================
    pedido = Pedido(
        numero_pedido=numero_pedido,
        cliente=cliente,
        fecha=datetime.utcnow(),
        costo_total=costo_total,
        usuario=usuario_actual,
        observaciones=observaciones,
        status_pedido=status_pedido.id
    )
    db.session.add(pedido)
    db.session.flush()  # 🆕 Obtiene pedido.id SIN hacer commit

    # ===========================================
    # DETALLES DEL PEDIDO + MOVIMIENTOS
    # ===========================================
    for item in detalles:
        color_id = item["color_id"]
        talla_id = item["talla_id"]
        cantidad_salida = item["cantidad"]

        inventario = Inventario.query.filter_by(
            color_id=color_id,
            talla_id=talla_id,
            status_id=estatus_en_inventario.id  # Origen: "En_Inventario", id = 5
        ).first()

        if not inventario:
            errores.append(f"No existe inventario disponible para Color {color_id}, Talla {talla_id}")
            continue

        if inventario.cantidad < cantidad_salida:
            errores.append(f"Cantidad insuficiente para Color {color_id}, Talla {talla_id}")
            continue

        # ===========================================
        # 🆕 Guardar línea del pedido en PedidoDetalle
        # ===========================================
        detalle_pedido = PedidoDetalle(
            pedido_id=pedido.id,
            color_id=color_id,
            talla_id=talla_id,
            cantidad=cantidad_salida,
            inventario_status_id=status_destino.id
        )
        db.session.add(detalle_pedido)

        # Descontar del inventario
        inventario.cantidad -= cantidad_salida

        registro_existente = Inventario.query.filter_by(
            color_id=color_id,
            talla_id=talla_id,
            status_id=status_destino.id
        ).first()

        if registro_existente:
            registro_existente.cantidad += cantidad_salida
            db.session.add(registro_existente)
        else:
            nuevo_registro = Inventario(
                color_id=color_id,
                talla_id=talla_id,
                cantidad=cantidad_salida,
                status_id=status_destino.id,
                usuario=usuario_actual
            )
            db.session.add(nuevo_registro)

        # Historial Inventario
        movimiento = HistorialInventario(
            inventario_id=inventario.id,
            tipo_movimiento="Preventa",
            cantidad_historial=cantidad_salida,
            status_id=status_destino.id,
            usuario=usuario_actual,
            observaciones=f"Lote de salida marcado como {status_pedido.nombre} en pedido #{numero_pedido}"
        )
        db.session.add(movimiento)

        # Historial Salidas
        salida = HistorialSalidas(
            inventario_id=inventario.id,
            status_salida_id=status_destino.id,
            cantidad=cantidad_salida,
            cliente=cliente,
            tipo_salida="Preventa",
            observaciones=f"Lote de salida marcado como {status_pedido.nombre} en pedido #{numero_pedido}",
            usuario=usuario_actual,
            fecha_salida=datetime.utcnow()
        )
        db.session.add(salida)

    # Manejo de errores
    if errores:
        db.session.rollback()
        return jsonify({"status": "error", "mensajes": errores}), 400
    
    # ===========================================
    # 🆕 GUARDAR HISTORIAL DE PEDIDO
    # ===========================================
    snapshot_detalles = []
    for item in detalles:
        talla = next((t for t in tallas if t.id == item["talla_id"]), None)
        costo_unitario = talla.costo if talla else 0

        snapshot_detalles.append({
            "color_id": item["color_id"],
            "talla_id": item["talla_id"],
            "cantidad": item["cantidad"],
            "costo_unitario": costo_unitario,
            "subtotal": costo_unitario * item["cantidad"]
        })

    historial = HistorialPedidos(
        pedido_id=pedido.id,
        accion="Surtido",
        status_pedido=status_pedido.id,  
        usuario=usuario_actual,
        costo_total=costo_total,
        detalles_json=json.dumps(snapshot_detalles)
    )
    db.session.add(historial)

    db.session.commit()
    return jsonify({"status": "ok", "mensaje": f"Lote procesado y marcado como '{status_pedido.nombre}"})



# ===============================
#   RUTA: Ver Pedidos
#===============================

@app.route("/pedidos")
@login_requerido
def ver_pedidos():
    pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()
    status_pedidos = (StatusPedido.query.order_by(StatusPedido.id.desc()).limit(3).all()[::-1])

    # Cálculo de totales por color
    totales_por_color = {}

    for pedido in pedidos:
        totales_por_color[pedido.id] = {}  # un diccionario por pedido

        for det in pedido.detalles:
            color = det.color.nombre
            cantidad = det.cantidad

            if color not in totales_por_color[pedido.id]:
                totales_por_color[pedido.id][color] = 0

            totales_por_color[pedido.id][color] += cantidad

    # Filtros
    estado_id = request.args.get("estado")
    numero_pedido = request.args.get("numero_pedido", "").strip()

    if estado_id and estado_id != "":
        pedidos = [p for p in pedidos if p.status_pedido == int(estado_id)]
    if numero_pedido:
        pedidos = [p for p in pedidos if str(p.numero_pedido) == numero_pedido]

    return render_template(
        "pedidos.html",
        pedidos=pedidos,
        status_pedidos=status_pedidos,
        totales_por_color=totales_por_color
    )


# ===============================
#   RUTA: Marcar Pedido como Vendido
#==============================
@app.route('/pedido_vendido/<int:pedido_id>', methods=['POST'])
def pedido_vendido(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    primer_historial = HistorialPedidos.query.filter_by(pedido_id=pedido_id).order_by(HistorialPedidos.fecha.asc()).first()

    detalles_json = primer_historial.detalles_json if primer_historial else None # Obtener detalles del primer historial si existe

    if not pedido:
        return jsonify({"status": "error", "mensaje": "Pedido no encontrado"}), 404

    usuario_actual = session.get("usuario", "Sistema")

    # Estatus "Vendidas" debe existir en tabla Status y "Vendido" en StatusPedido
    status_vendidas = Status.query.filter_by(nombre="Vendidas").first()
    status_pedido_vendido = StatusPedido.query.filter_by(nombre="Vendido").first()

    if not status_vendidas or not status_pedido_vendido:
        return jsonify({"status": "error", "mensaje": "No existe el estatus 'Vendidas'"}), 400

    errores = []

    # Procesar cada detalle del pedido
    for det in pedido.detalles:

        inventario_origen = Inventario.query.filter_by(
            color_id=det.color_id,
            talla_id=det.talla_id,
            status_id=det.inventario_status_id
        ).first()

        if not inventario_origen:
            errores.append(
                f"No se encontró inventario para Color {det.color_id}, Talla {det.talla_id}"
            )
            continue

        if inventario_origen.cantidad < det.cantidad:
            errores.append(
                f"Inventario insuficiente para Color {det.color_id}, Talla {det.talla_id}"
            )
            continue

        # Descuenta en origen
        inventario_origen.cantidad -= det.cantidad

        # Agrega a Vendidas
        inventario_destino = Inventario.query.filter_by(
            color_id=det.color_id,
            talla_id=det.talla_id,
            status_id=status_vendidas.id
        ).first()

        if inventario_destino:
            inventario_destino.cantidad += det.cantidad
        else:
            inventario_destino = Inventario(
                color_id=det.color_id,
                talla_id=det.talla_id,
                cantidad=det.cantidad,
                status_id=status_vendidas.id,
                usuario=usuario_actual
            )
            db.session.add(inventario_destino)

        # Actualizar status_id del detalle
        det.inventario_status_id = status_vendidas.id
        db.session.add(det)

        # HistorialInventario
        mov = HistorialInventario(
            inventario_id=inventario_origen.id,
            tipo_movimiento="Ventas",
            cantidad_historial=det.cantidad,
            status_id=status_vendidas.id,
            usuario=usuario_actual,
            observaciones=f"Pedido #{pedido.numero_pedido} marcado como: Vendido"
        )
        db.session.add(mov)

        # HistorialSalidas
        salida = HistorialSalidas(
            inventario_id=inventario_origen.id,
            status_salida_id=status_vendidas.id,
            cantidad=det.cantidad,
            cliente=pedido.cliente,
            tipo_salida="Ventas",
            observaciones=f"Pedido #{pedido.numero_pedido} marcado como: Vendido",
            usuario=usuario_actual,
            fecha_salida=datetime.utcnow()
        )
        db.session.add(salida)

    # Si hubo errores, cancelar toda la transacción
    if errores:
        db.session.rollback()
        return jsonify({"status": "error", "mensajes": errores}), 400

    # Si ya está vendido, no lo proceses nuevamente
    if pedido.status_pedido == status_pedido_vendido.id:
        return jsonify({"status": "warning", "mensaje": "Este pedido ya estaba marcado como vendido."}), 200


    # Cambiar estatus del pedido
    pedido.status_pedido = status_pedido_vendido.id
    db.session.add(pedido)

    # ===================================================
    #   🔵 REGISTRAR EN HISTORIALPEDIDOS
    # ===================================================

    registro = HistorialPedidos(
        pedido_id=pedido.id,
        accion="Vendido",
        status_pedido=status_pedido_vendido.id,  # Estatus "Vendido" en StatusPedido
        usuario=usuario_actual,
        fecha=datetime.utcnow(),
        detalles_json=detalles_json,  # Usar el mismo snapshot de detalles
        costo_total=pedido.costo_total
    )
    db.session.add(registro)
    # ===================================================
    #   🔵 GUARDAR CAMBIOS
    # ===================================================
    db.session.commit()

    return jsonify({"status": "ok", "mensaje": "Pedido vendido y registrado en historial correctamente"})

# ===============================
#   RUTA: Cancelar Pedido
#===============================

@app.route("/pedido_cancelar/<int:pedido_id>", methods=["POST"])
def pedido_cancelar(pedido_id):

    pedido = Pedido.query.get(pedido_id)
    primer_historial = HistorialPedidos.query.filter_by(pedido_id=pedido_id).order_by(HistorialPedidos.fecha.asc()).first()
    status_pedido_cancelado = StatusPedido.query.filter_by(nombre="Cancelado").first()
    status_en_inventario = Status.query.filter_by(nombre="En_Inventario").first()
    status_surtidas = Status.query.filter_by(nombre="Surtidas").first()
    status_devueltas = Status.query.filter_by(nombre="Devueltas").first()


    detalles_json = primer_historial.detalles_json if primer_historial else None # Obtener detalles del primer historial si existe

    if not pedido: # Si NO existe el pedido
        return jsonify({"status": "error", "mensaje": "Pedido no encontrado."}), 404

    # 🚫 NO cancelar pedidos vendidos
    if pedido.status_pedido == "Vendido":
        return jsonify({
            "status": "error",
            "mensaje": "No puedes cancelar un pedido que ya está marcado como VENDIDO."
        }), 400
    
    usuario_actual = session.get("usuario", "Sistema")

    # ------------------------------------------------------------    
    # 🔄 1. Cambiar estatus del pedido y de pedido_detalle
    # ------------------------------------------------------------
    pedido.status_pedido = status_pedido_cancelado.id  # Estatus "Cancelado" en StatusPedido
    pedido.observaciones = (pedido.observaciones or "") + ", \nPedido cancelado."
    db.session.add(pedido)

    for det in pedido.detalles: # Recorrer Los detalles del pedido
        det.inventario_status_id = status_en_inventario.id # Cambiar a Estatus "En_Inventario" en Status de Inventario cada detalle
        db.session.add(det)



    # ------------------------------------------------------------
    # 🔄 2. Recorrer detalles del pedido y devolver stock
    # ------------------------------------------------------------
    for d in pedido.detalles:

        # Buscar inventario con estatus "Surtidas" para restar la devolución 
        inventario_origen = Inventario.query.filter_by(
            color_id=d.color_id,
            talla_id=d.talla_id,
            status_id=status_surtidas.id,    # BUSCART Estatus "Surtidas" o "Apartadas" en Status de Inventario
        ).first()

        if inventario_origen:
            inventario_origen.cantidad -= d.cantidad # Restar la cantidad devuelta al estatus "Surtidas" o "Apartadas"
            db.session.add(inventario_origen)

        # Buscar inventario con estatus "En_Inventario" para sumar la devolución
        inventario_destino = Inventario.query.filter_by(
            color_id=d.color_id,
            talla_id=d.talla_id,
            status_id=status_en_inventario.id,    # Estatus "En Inventario" en Status de Inventario
        ).first()

        if inventario_destino:
            inventario_destino.cantidad += d.cantidad # Sumar la cantidad devuelta al inventario
            db.session.add(inventario_destino)

        # Historial Inventario
        movimiento = HistorialInventario(
            inventario_id=inventario_destino.id,
            tipo_movimiento="Devolución",
            cantidad_historial=d.cantidad,
            status_id=status_devueltas.id,  # estatus "Devueltas" en Status de Inventario
            usuario=usuario_actual,
            observaciones=f"Devolución de pedido #{pedido.numero_pedido}, Cancelado."
        )
        db.session.add(movimiento)
   
    # ------------------------------------------------------------
    # 🔄 3. Registrar en HistorialPedidos
    # ------------------------------------------------------------
    registro = HistorialPedidos(
        pedido_id=pedido.id,
        accion="Cancelado",
        status_pedido=status_pedido_cancelado.id,  # Estatus "Cancelado" en StatusPedido
        usuario=usuario_actual,
        fecha=datetime.utcnow(),
        detalles_json=detalles_json, # Usar el mismo snapshot de detalles
        costo_total=pedido.costo_total
    )
    db.session.add(registro)

    # ------------------------------------------------------------
    # 🔄 4. Guardar cambios
    # ------------------------------------------------------------
    db.session.commit()

    return jsonify({
        "status": "ok",
        "mensaje": "Pedido cancelado y stock devuelto correctamente."
    })

# ===============================
#   RUTA: Consulta
#===============================

@app.route("/consulta")
@login_requerido
def consulta():

    color_id = request.args.get("color_id")
    talla_id = request.args.get("talla_id")


    colores = Color.query.all()
    tallas = Talla.query.all()
    estados = Status.query.all()

    status_en_inventario = Status.query.filter_by(nombre="En_Inventario").first()
  

    # Consulta base de inventario
    inventarios = db.session.query(Inventario).join(Color).join(Talla).join(Status)
    inventarios = inventarios.order_by(Talla.id.asc())
    inventarios = inventarios.filter(Inventario.status_id == status_en_inventario.id, Inventario.cantidad > 0) #Estatus de "En_Inventario"

    # Aplicar filtros
    if color_id and color_id != "":
        inventarios = inventarios.filter(Inventario.color_id == color_id)
    if talla_id and talla_id != "":
        inventarios = inventarios.filter(Inventario.talla_id == talla_id)

    inventarios = inventarios.all()

    # Agrupamiento cuando solo se selecciona la talla
    inventarios_agrupados = {}

    for inv in inventarios:
        color = inv.color.nombre
        if color not in inventarios_agrupados:
            inventarios_agrupados[color] = []
        inventarios_agrupados[color].append(inv)

    # 🔥 FILTRAR: solo colores que tengan tallas en inventario
    colores_con_inventario = {inv.color_id for inv in inventarios}
    colores = [c for c in colores if c.id in colores_con_inventario]

    return render_template(
        "consulta.html",
        colores=colores,
        tallas=tallas,
        estados=estados,
        inventarios=inventarios,
        color_seleccionado=color_id,
        talla_seleccionada=talla_id, inventarios_agrupados=inventarios_agrupados,
    )

# ==============================
#   RUTA: Generar PDF de Pedido
# ==============================

@app.route("/pedido/<int:pedido_id>/imprimir")
@login_requerido
def vista_previa_pedido(pedido_id):

    pedido = Pedido.query.get_or_404(pedido_id)


    return render_template(
        "pedido_impresion.html",
        pedido=pedido,
    )



if __name__ == "__main__":
    app.run(debug=True)
