# Book Manager

**Trabajo Práctico Integrador** — Seminario de Actualización I (Lic. en Ciencia de Datos, UGR) — Grupo 39

## Sprint actual

**Sprint 2**

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y en
el almacenamiento de datos para su persistencia, consolidando las bases del
manejo de bases de datos relacionales: normalización, conexión segura y carga
inicial.

## Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión
de inventario de libros. Debido a la fluctuación en los costos de importación
de material bibliográfico, el sistema gestiona precios en diferentes monedas y
sigue de cerca la cotización del dólar.

En el Sprint 1 se desarrolló una aplicación de consola (CLI) en Python, con
persistencia en archivos CSV, que permite gestionar el inventario, cotizar los
libros según el valor del dólar y comparar precios con la competencia web
(tomando como referencia el sitio Cúspide).

En el Sprint 2 se amplía el alcance:

- La aplicación pasa a persistir en una base de datos relacional
  (PostgreSQL en Supabase), usando SQLAlchemy. La conexión se configura en
  el archivo `.env`; sin esas credenciales, el sistema usa una base SQLite
  local.
- Los datos cargados en los archivos del Sprint 1 se migran a tablas
  relacionales, generando los archivos `.sql` de inserción.
- Las cotizaciones del dólar se obtienen de una API externa, cuya URL
  también se configura en el archivo `.env`.
- La consola suma la obtención de cotizaciones por API, la lista de precios
  bimonetaria y la exportación de precios a CSV.

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
│       ├── database/connection.py
│       ├── entities/entities.py
│       ├── models/models.py
│       ├── preload_data/preload_data.py
│       ├── repositories/repositories.py
│       ├── services/services.py
│       ├── migrations/
│       │   ├── csv/
│       │   ├── sql/
│       │   └── migrations.py
│       ├── ui/console.py
│       └── main.py
├── .env
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
