# OscarDev UI Components

> Biblioteca de componentes reutilizables desarrollada para aplicaciones Flask + Bootstrap.

**Versión:** 1.0

**Autor:** Oscar Espinosa Torres

---

# Objetivo

OscarDev UI Components nace con el propósito de proporcionar una colección de componentes reutilizables, modernos y consistentes para todos los proyectos desarrollados por Oscar Espinosa Torres.

La filosofía del proyecto es:

- Mantener una experiencia de usuario uniforme.
- Evitar código duplicado.
- Centralizar estilos y comportamiento.
- Facilitar el mantenimiento.
- Reducir el tiempo de desarrollo en proyectos futuros.

---

# Componentes incluidos

## 1. Loading Buttons

**Archivos**

```
static/js/loading-buttons.js
```

### Objetivo

Evitar el envío múltiple de formularios y proporcionar retroalimentación visual inmediata al usuario.

### Funcionalidades

✔ Deshabilita automáticamente el botón al enviar un formulario.

✔ Evita dobles clics.

✔ Muestra un spinner Bootstrap.

✔ Cambia dinámicamente el texto del botón.

✔ Permite personalizar el mensaje mediante:

```html
data-loading-text="Guardando..."
```

✔ Funciona con cualquier formulario simplemente agregando:

```html
class="btn-loading"
```

---

## 2. Loading Overlay

**Archivos**

```
static/js/loading-overlay.js

static/css/loading-overlay.css
```

### Objetivo

Bloquear completamente la interfaz mientras se ejecutan procesos importantes.

### Funcionalidades

✔ Bloquea toda la pantalla.

✔ Evita múltiples acciones simultáneas.

✔ Oscurece el fondo.

✔ Muestra spinner centrado.

✔ Permite mensajes personalizados.

Ejemplo:

```javascript
mostrarOverlay("Registrando pedido...");
```

o

```javascript
mostrarOverlay("Actualizando inventario...");
```

✔ Compatible con cualquier operación AJAX.

---

## 3. Toast Notifications

**Archivos**

```
static/js/toast-notifications.js

static/css/toast-notifications.css
```

### Objetivo

Mostrar mensajes temporales sin interrumpir el flujo de trabajo del usuario.

### Tipos soportados

✔ Success

✔ Error

✔ Warning

✔ Info

### Características

✔ Diseño propio.

✔ Responsive.

✔ Posición fija.

✔ Auto ocultado.

✔ Animación de entrada.

✔ Animación de salida.

✔ No utiliza alert() del navegador.

Ejemplo:

```javascript
mostrarToast("Pedido registrado correctamente","success");
```

---

## 4. Confirm Modal

**Archivos**

```
static/js/confirm-modal.js
```

### Objetivo

Solicitar confirmación del usuario antes de ejecutar acciones críticas.

### Funcionalidades

✔ Modal reutilizable.

✔ Callback personalizado.

✔ Cambia automáticamente:

- título
- botón
- color
- icono

✔ Compatible con:

- Eliminar
- Cancelar
- Confirmar
- Marcar vendido
- Procesos futuros

Ejemplo

```javascript
confirmarAccion({

    titulo:"Cancelar pedido",

    mensaje:"¿Deseas continuar?",

    color:"danger",

    textoBoton:"Sí, cancelar",

    onConfirm:function(){

        cancelarPedido();

    }

});
```

---

## 5. Modal Premium

**Archivos**

```
static/css/modal-premium.css
```

### Objetivo

Proporcionar un diseño uniforme para todos los modales del sistema.

### Características

✔ Bordes redondeados.

✔ Sombras suaves.

✔ Header consistente.

✔ Footer uniforme.

✔ Botones estandarizados.

✔ Responsive.

✔ Compatible con Bootstrap.

### Tipos soportados

✔ Primary

✔ Success

✔ Danger

✔ Warning

---

# Convenciones

Todos los proyectos nuevos deberán utilizar estos componentes antes de crear soluciones específicas.

No deberán utilizarse:

❌ alert()

❌ confirm()

❌ prompt()

excepto durante pruebas rápidas de desarrollo.

---

# Beneficios

✔ Código reutilizable.

✔ Mantenimiento sencillo.

✔ Mejor experiencia de usuario.

✔ Apariencia consistente.

✔ Escalable.

✔ Fácil integración en nuevos proyectos.

---

# Proyectos que utilizan OscarDev UI Components

- Sistema de Inventario para Abarrotes
- Sistema de Producción (próximamente)
- Hotel Analytics Platform (próximamente)

---

# Roadmap

## Versión 1.1

- Buttons Premium
- Badges Premium
- Cards Premium

## Versión 1.2

- Tables Premium
- Empty States
- Formularios Premium

## Versión 2.0

- Dashboard Components
- Charts Components
- Date Picker
- Buscador Inteligente
- Modo Oscuro

---

# Filosofía

OscarDev UI Components busca que cada nuevo proyecto tenga una apariencia moderna, consistente y profesional, permitiendo concentrar el esfuerzo en la lógica del negocio y no en volver a construir los mismos componentes visuales.