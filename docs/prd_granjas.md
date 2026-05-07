# PRD Simplificado — Gestión de Granjas (v1)

## Overview

La aplicación permite a una granja registrar y entender su operación diaria a través de unidades productivas y eventos. El sistema debe ser flexible para distintos tipos de animales, pero simple de usar en casos comunes como gallinas o vacas.

---

## Modelo Conceptual

Todo parte de una **granja (workspace)**.
Dentro de la granja existen **unidades productivas**, que representan grupos o categorías definidas por el usuario, como:

- Gallinas
- Vacas lecheras
- Ovejas

Las unidades productivas no tienen lógica rígida asociada. Son contenedores donde ocurre la actividad.

Cada unidad puede operar de dos formas:

- **Modo agregado** (sin individuos)
- **Modo individual** (con animales identificables)

Los **individuos** son opcionales y se usan solo cuando tiene sentido (ej: vacas). Cada individuo puede tener atributos como nombre, tag o identificación.

---

## Eventos (Core del sistema)

Todo lo que ocurre en la granja se registra como un **evento**.

Un evento pertenece a:

- una granja
- una unidad productiva
- opcionalmente, a un individuo

Cada evento tiene:

- tipo (definido por el sistema)
- categoría (definida por el usuario)
- fecha
- cantidad o valor
- notas opcionales

---

## Tipos de Eventos

El sistema define tipos base para mantener consistencia:

### Producción
Registra lo que se genera.

Ejemplos:
- huevos
- leche
- lana

---

### Gasto
Registra costos asociados.

Ejemplos:
- alimento
- medicación
- mantenimiento

---

### Ingreso
Registra entradas de dinero.

Ejemplos:
- venta de huevos
- venta de animales

---

### Evento Sanitario / Físico
Registra estado o mediciones.

Ejemplos:
- peso
- enfermedad
- tratamiento

---

### Evento Reproductivo
Aplica a animales individuales.

Ejemplos:
- nacimiento (cría)
- fertilización
- registro de madre/padre

---

## Categorías

Las categorías son definidas por el usuario.

Ejemplos:
- "huevos", "leche", "lana"
- "alimento balanceado", "maíz"
- "venta feria", "venta directa"

Esto permite adaptar el sistema sin modificar el backend.

---

## Diferenciación de Casos

### Gallinas (modo agregado)

- Se crea una unidad productiva: "Gallinas"
- No se crean individuos
- Todos los eventos son a nivel grupo

Ejemplo:
- Producción: 120 huevos/día

---

### Vacas (modo individual)

- Se crea una unidad productiva: "Vacas"
- Se crean individuos (Vaca A, Vaca B, etc.)

Los eventos pueden ser:
- a nivel unidad (ej: gasto de alimento)
- a nivel individuo (ej: peso de Vaca A)

---

## Relaciones entre Individuos

Para soportar casos como parentesco:

- Los individuos pueden referenciarse entre sí
- Ejemplo:
  - madre → cría
  - padre → cría

Esto se maneja como relaciones simples entre registros.

---

## Principios de Diseño

- Simplicidad sobre perfección
- No modelar reglas complejas innecesarias
- Evitar estructuras rígidas por tipo de animal
- Basarse en unidades + eventos + categorías
- Permitir agregar nuevos casos sin cambios en backend

---

## Resultado Esperado

El usuario puede:

- Registrar actividad diaria sin fricción
- Ver producción, gastos e ingresos
- Analizar datos por unidad o individuo
- Adaptar el sistema a su realidad sin soporte técnico
