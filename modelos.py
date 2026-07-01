from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils import fecha_local_tijuana



db = SQLAlchemy()

# ==========================
#   MODELO: COLORES
# ==========================
class Color(db.Model):
    __tablename__ = "color"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)


    cortes = db.relationship("Corte", back_populates="color")  # 🔥 aquí
    inventarios = db.relationship("Inventario", back_populates="color")  # 🆕 aquí

    def __repr__(self):
        return f"<Color {self.nombre}>"
    


# ==========================
#   MODELO: TALLAS
# ==========================
class Talla(db.Model):
    __tablename__ = "talla"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(10), unique=True, nullable=False)
    costo = db.Column(db.Float, nullable=False, default=0.0)

    producciones = db.relationship("Produccion", back_populates="talla")

    def __repr__(self):
        return f"<Talla {self.nombre}>"

# ==========================
#   MODELO: CORTE
# ==========================
class Corte(db.Model):
    __tablename__ = "corte"
    id = db.Column(db.Integer, primary_key=True)
    # Fecha real del corte físico (editable por el usuario)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    numero_corte = db.Column(db.String(20), nullable=False, unique=True)
    metros = db.Column(db.Float, nullable=False)
    cantidad_corte = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default="por_coser")
    color_id = db.Column(db.Integer, db.ForeignKey("color.id"), nullable=False)

    # Relación con Color
    color = db.relationship("Color", back_populates="cortes")

    # Relación con Produccion (borrado en cascada)
    producciones = db.relationship(
        "Produccion",
        back_populates="corte",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # ✅ Relación con HistorialProduccion (sin cascada)
    # No se usa delete-orphan ni cascade aquí para conservar el historial.
    historial = db.relationship(
        "HistorialProduccion",
        primaryjoin="Corte.id==foreign(HistorialProduccion.corte_id)",
        back_populates="corte",
        passive_deletes=True  # permite SET NULL pero no borra los historiales
    )

    def __repr__(self):
        return f"<Corte #{self.numero_corte} ({self.color.nombre})>"


# ==========================
#   MODELO: PRODUCCIÓN
# ==========================
class Produccion(db.Model):
    __tablename__ = "produccion"
    id = db.Column(db.Integer, primary_key=True)
    talla_id = db.Column(db.Integer, db.ForeignKey("talla.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)

    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    corte_id = db.Column(db.Integer, db.ForeignKey("corte.id", ondelete="CASCADE"), nullable=False)

    # 🟢 Fecha del corte físico (sincronizada con Corte.fecha)
    fecha_corte = db.Column(db.Date, nullable=False)

    # 🟡 Fecha real de registro en el sistema (auditoría)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    talla = db.relationship("Talla")
    status = db.relationship("Status")

    # Relación con Corte (hereda color desde aquí)
    corte = db.relationship("Corte", back_populates="producciones")

    @property
    def color(self):
        """Devuelve el color heredado del corte asociado."""
        return self.corte.color if self.corte else None

    def __repr__(self):
        color_nombre = self.corte.color.nombre if self.corte and self.corte.color else "Sin color"
        return f"<Produccion {self.status.nombre} {color_nombre} {self.talla.nombre} x{self.cantidad}>"


# ==========================
#   MODELO: HISTORIAL DE PRODUCCIÓN
# ==========================
class HistorialProduccion(db.Model):
    __tablename__ = "historial_produccion"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ Mantener el corte_id incluso si el corte es eliminado
    corte_id = db.Column(
        db.Integer,
        db.ForeignKey("corte.id", ondelete="SET NULL"),  # SET NULL evita errores de FK
        nullable=True
    )

    historial_numero_corte = db.Column(db.Integer)
    historial_talla = db.Column(db.String(5), nullable=False)
    historial_color = db.Column(db.String(30), nullable=False)
    historial_cantidad = db.Column(db.Integer, nullable=False)
    historial_status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    historial_status = db.relationship("Status", backref="historial")

    fecha_status = db.Column(db.DateTime, default=fecha_local_tijuana, nullable=False)
    usuario = db.Column(db.String(50), default="sistema")
    observacion = db.Column(db.Text, nullable=True)

    # ✅ Relación de solo lectura para conservar referencia lógica del corte
    corte = db.relationship(
        "Corte",
        primaryjoin="foreign(HistorialProduccion.corte_id)==Corte.id",
        back_populates="historial",
        viewonly=True  # evita que SQLAlchemy intente modificar corte_id
    )

    def __repr__(self):
        return f"<Historial Corte#{self.historial_numero_corte} Talla:{self.historial_talla} {self.historial_status.nombre}>"
   
# ==========================
#   MODELO: STATUS PRODUCCION E INVENTARIO
# ==========================
class Status(db.Model):
    __tablename__ = "status"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.String(100), nullable=True)
    fase = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Status {self.nombre}>"
    
# ==========================
#   MODELO: STATUS PEDIDOS  
# ==========================
class StatusPedido(db.Model):
    __tablename__ = "status_pedido"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(30), unique=True, nullable=False)
    descripcion = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<StatusPedido {self.nombre}>"
    

# ==========================
#   MODELO: USUARIOS DEL SISTEMA
# ==========================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    rol = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.nombre} - Rol:{self.rol}>"
    
# ==========================
#   MODELO: INVENTARIO
# ==========================
class Inventario(db.Model):
    __tablename__ = "inventario"

    id = db.Column(db.Integer, primary_key=True)
    color_id = db.Column(db.Integer, db.ForeignKey("color.id"), nullable=False)
    talla_id = db.Column(db.Integer, db.ForeignKey("talla.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    usuario = db.Column(db.String(50), default="sistema")
    observaciones = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.DateTime, default=fecha_local_tijuana, onupdate=datetime.utcnow)

    # Relaciones
        # Relación con Color
    color = db.relationship("Color", back_populates="inventarios")
    talla = db.relationship("Talla")
    status = db.relationship("Status")
    movimientos = db.relationship("HistorialInventario", back_populates="inventario", cascade="all, delete-orphan")
    salidas = db.relationship("HistorialSalidas", back_populates="inventario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inventario {self.color.nombre} {self.talla.nombre} ({self.status.nombre}) x{self.cantidad}>"



# ==========================
#   MODELO: HISTORIAL INVENTARIO
# ==========================
class HistorialInventario(db.Model):
    __tablename__ = "historial_inventario"

    id = db.Column(db.Integer, primary_key=True)
    inventario_id = db.Column(db.Integer, db.ForeignKey("inventario.id", ondelete="CASCADE"))
    tipo_movimiento = db.Column(
        db.Enum("Recepción Producción", "Ingreso Manual", "Devolución", "Ajuste Alta", "Ajuste Baja", "Salidas", "Preventa", "Ventas"),
        nullable=False
    )
    cantidad_historial = db.Column(db.Integer, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    fecha_movimiento = db.Column(db.DateTime, default=fecha_local_tijuana, nullable=False)
    usuario = db.Column(db.String(50), default="sistema")
    observaciones = db.Column(db.Text, nullable=True)
    

    # Relaciones
    inventario = db.relationship("Inventario", back_populates="movimientos")
    status = db.relationship("Status")

    def __repr__(self):
        return f"<Movimiento {self.tipo_movimiento} {self.cantidad_historial} ({self.status.nombre})>"
    

# ==========================
#   MODELO: HISTORIAL SALIDAS
# ==========================

class HistorialSalidas(db.Model):
    __tablename__ = "historial_salidas"

    id = db.Column(db.Integer, primary_key=True)
    # Relación con inventario
    inventario_id = db.Column(db.Integer, db.ForeignKey("inventario.id"), nullable=False)
    # Estado de la salida (ej. Surtida, Apartada, Donada, Dañada, etc.)
    status_salida_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    # Cantidad de prendas que salieron del inventario
    cantidad = db.Column(db.Integer, nullable=False)
    # Nombre o identificador del cliente (opcional)
    cliente = db.Column(db.String(100), nullable=True)
    # Motivo o referencia (ej. "Pedido #102", "Daño por humedad", etc.)
    tipo_salida = db.Column(db.String(100), nullable=True)
    # Observaciones internas o notas
    observaciones = db.Column(db.Text, nullable=True)
    # Usuario que realizó el movimiento
    usuario = db.Column(db.String(50), default="sistema")
    # Fecha y hora del movimiento
    fecha_salida = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    inventario = db.relationship("Inventario", back_populates="salidas")
    status_salida = db.relationship("Status")

    def __repr__(self):
        return (
            f"<HistorialSalidas InvID={self.inventario_id}, "
            f"Estado={self.status_salida.nombre}, "
            f"Cliente={self.cliente or 'N/A'}, "
            f"Cant={self.cantidad}>"
        )

# ==========================
#   MODELO: LOTES DE PEDIDOS 
# ==========================
class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)

    numero_pedido = db.Column(db.Integer, nullable=False)

    cliente = db.Column(db.String(100), nullable=True)

    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    costo_total = db.Column(db.Float, nullable=False, default=0.0)

    observaciones = db.Column(db.Text, nullable=True)

    usuario = db.Column(db.String(50), default="sistema")

    # 🔥 Nuevo estatus del pedido (independiente del inventario)
    status_pedido = db.Column(db.Integer, db.ForeignKey("status_pedido.id"), nullable=False)

    def __repr__(self):
        return f"<Pedido #{self.numero_pedido} - {self.status_pedido}>"

# ==========================
#  MODELO: DETALLES DE PEDIDOS
# =========================
# Detalle específico dentro de un pedido, asociando color, talla y cantidad.
# Cada pedido puede tener múltiples detalles.
# =========================    
class PedidoDetalle(db.Model):
    __tablename__ = "pedido_detalles"

    id = db.Column(db.Integer, primary_key=True)

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False
    )

    color_id = db.Column(
        db.Integer,
        db.ForeignKey("color.id"),
        nullable=False
    )

    talla_id = db.Column(
        db.Integer,
        db.ForeignKey("talla.id"),
        nullable=False
    )

    cantidad = db.Column(db.Integer, nullable=False)

    # 🔥 Campo necesario para saber desde qué estatus salió cada prenda
    inventario_status_id = db.Column(
        db.Integer,
        db.ForeignKey("status.id"),
        nullable=False
    )

    # Relaciones
    pedido = db.relationship("Pedido", backref="detalles")
    color = db.relationship("Color")
    talla = db.relationship("Talla")
    status = db.relationship("Status")  # Opcional, pero útil

    def __repr__(self):
        return (
            f"<Detalle Pedido {self.pedido_id}: "
            f"{self.color.nombre} {self.talla.nombre} x{self.cantidad} "
            f"status:{self.inventario_status_id}>"
        )
    
# ==============================
#   MODELO: HISTORIAL DE PEDIDOS
# ==============================
class HistorialPedidos(db.Model):
    __tablename__ = "historial_pedidos"

    id = db.Column(db.Integer, primary_key=True)

    # Relación con el pedido original
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False
    )

    # Acción registrada: "Creado", "Surtido", "Vendido", "Cancelado"
    accion = db.Column(db.String(50), nullable=False)

    status_pedido = db.Column(db.Integer, db.ForeignKey("status_pedido.id"), nullable=False)

    # Usuario que realizó la acción
    usuario = db.Column(db.String(50), nullable=False, default="sistema")

    # Fecha del movimiento
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Guarda una copia de los detalles del pedido
    detalles_json = db.Column(db.Text, nullable=True)

    # Guarda el costo total en ese momento
    costo_total = db.Column(db.Float, nullable=False, default=0.0)

    # Relación opcional para consultar desde "/ver_pedido/<id>"
    pedido = db.relationship("Pedido")

    def __repr__(self):
        return f"<HistorialPedido {self.pedido_id} - {self.accion}>"