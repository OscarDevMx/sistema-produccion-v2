# Sistema de Producción v2.0

Proyecto en proceso de migración de SQLite a MySQL.

Estado actual:
- Preparación del proyecto.
- Migración a MySQL (en desarrollo).

## Estructura del Proyecto

```
sistema_produccion-v2.0/
│
├── app.py                          # Aplicación principal Flask
├── config.py                       # Configuración de la aplicación
├── extensions.py                   # Extensiones (DB, SQLAlchemy)
├── modelos.py                      # Modelos de base de datos
├── utils.py                        # Funciones utilitarias
├── requirements.txt                # Dependencias de Python
├── README.md                       # Este archivo
│
├── routes/                         # Rutas y controladores
│   ├── __init__.py
│   ├── auth.py                     # Autenticación
│   ├── catalogos.py                # Gestión de catálogos
│   ├── colores.py                  # Gestión de colores
│   ├── inicio.py                   # Página de inicio
│   └── tallas.py                   # Gestión de tallas
│
├── templates/                      # Plantillas HTML
│   ├── base.html                   # Plantilla base
│   ├── colores.html                # Listado de colores
│   ├── consulta.html               # Consultas
│   ├── editar_color.html           # Edición de colores
│   ├── ingreso_manual.html         # Ingreso manual
│   ├── inicio.html                 # Dashboard
│   ├── inventario_disponible.html  # Inventario disponible
│   ├── inventario_general.html     # Inventario general
│   ├── login.html                  # Página de login
│   ├── pedido_impresion.html       # Pedidos de impresión
│   ├── pedido_mobile.html          # Pedidos versión mobile
│   ├── pedidos.html                # Gestión de pedidos
│   ├── surtido.html                # Surtidos
│   └── ver_historial_inventario.html # Historial de inventario
│
├── static/                         # Archivos estáticos
│   ├── css/                        # Estilos CSS
│   ├── js/                         # Scripts JavaScript
│   └── images/                     # Imágenes y recursos
│
└── util/                           # Utilidades
    └── decorators.py               # Decoradores personalizados


```

