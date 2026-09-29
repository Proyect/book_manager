# Book Manager

**Trabajo Práctico Integrador** — Seminario de Actualización I (Lic. en Ciencia de Datos, UGR) — Grupo 39

## Sprint actual

**Sprint 1**

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y en el almacenamiento de datos en archivos para su persistencia.

## Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

En este sprint se desarrolla una aplicación de consola (CLI) en Python que permite gestionar el inventario de la librería, cotizar los libros según el valor del dólar y comparar precios con la competencia web (tomando como referencia el sitio Cúspide).

### Entidades

- **Libro**: cada título del catálogo (ISBN, título, autor, editorial, género, etc.).
- **Genero**: categoría literaria a la que pertenece un libro.
- **Editorial**: proveedor/distribuidora que provee los libros.
- **Moneda**: monedas en las que se expresa un precio (ARS, USD, etc.).
- **TipoCotizacion**: tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- **Precio**: valor monetario de un libro en una moneda determinada.
- **Stock**: cantidad disponible de cada libro.
- **CotizacionDolar**: registro histórico de cotizaciones por tipo y fecha.

## Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── entities/entities.py
│       ├── preload_data/preload_data.py
│       ├── repositories/repositories.py
│       ├── services/services.py
│       ├── migrations/csv/
│       ├── ui/console.py
│       └── main.py
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## Integrantes

- Ariel Marcelo Diaz
- Marco Fouad Abboud
- Matias Gabriel Gallardo
- Nestor Fabian Leon
- Sebastian Luna
