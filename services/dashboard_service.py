from sqlalchemy import func

from modelos import (
    db,
    Color,
    Inventario,
    Status,
    Pedido,
    StatusPedido,
    HistorialSalidas,
    PedidoDetalle
)


def obtener_kpis_dashboard():
    """
    Obtiene los indicadores principales del Dashboard.
    """
    colores_registrados = Color.query.count()

    status_inventario = Status.query.filter_by(
        nombre="En_Inventario"
    ).first()

    inventario_disponible = 0

    if status_inventario:
        inventario_disponible = (
            db.session.query(
                func.coalesce(func.sum(Inventario.cantidad), 0)
            )
            .filter(
                Inventario.status_id == status_inventario.id
            )
            .scalar()
        )

    status_vendido = StatusPedido.query.filter_by(
        nombre="Vendido"
    ).first()

    ingresos_totales = 0

    if status_vendido:
        ingresos_totales = (
            db.session.query(
                func.coalesce(func.sum(Pedido.costo_total), 0)
            )
            .filter(
                Pedido.status_pedido == status_vendido.id
            )
            .scalar()
        )

    status_prendas_vendidas = Status.query.filter_by(
        nombre="Vendidas"
    ).first()

    prendas_vendidas = 0

    if status_prendas_vendidas:
        prendas_vendidas = (
            db.session.query(
                func.coalesce(func.sum(HistorialSalidas.cantidad), 0)
            )
            .filter(
                HistorialSalidas.status_salida_id == status_prendas_vendidas.id
            )
            .scalar()
        )

    return {
        "colores_registrados": colores_registrados,
        "inventario_disponible": inventario_disponible,
        "ingresos_totales": ingresos_totales,
        "prendas_vendidas": prendas_vendidas
    }

def obtener_ventas_recientes():

    status_vendido = StatusPedido.query.filter_by(
        nombre="Vendido"
    ).first()

    if not status_vendido:
        return []

    pedidos = (
        Pedido.query
        .filter(Pedido.status_pedido == status_vendido.id)
        .order_by(Pedido.fecha.desc())
        .limit(3)
        .all()
    )

    pedido_ids = [pedido.id for pedido in pedidos]

    if not pedido_ids:
        return []

    ventas = (
        PedidoDetalle.query
        .join(Pedido)
        .filter(PedidoDetalle.pedido_id.in_(pedido_ids))
        .order_by(
            Pedido.fecha.desc(),
            Pedido.numero_pedido.desc(),
            PedidoDetalle.color_id,
            PedidoDetalle.talla_id
        )
        .all()
    )
    
    ventas_por_pedido = []

    for pedido in pedidos:

        detalles = [
            v for v in ventas
            if v.pedido_id == pedido.id
        ]

        total_prendas = sum(
            d.cantidad
            for d in detalles
        )

        ventas_por_pedido.append({

            "pedido": pedido,

            "detalles": detalles,

            "total_prendas": total_prendas

        })

    return ventas_por_pedido

def obtener_dashboard():

    return {
        "kpis": obtener_kpis_dashboard(),
        "ventas_recientes": obtener_ventas_recientes()
    }