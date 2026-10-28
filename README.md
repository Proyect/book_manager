# Book Manager

**Trabajo Práctico Integrador** — Seminario de Actualización I (Lic. en Ciencia de Datos, UGR) — Grupo 39

## Sprint actual

**Sprint 3**

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y en
el almacenamiento de datos para su persistencia, incorporando la obtención de
datos de la web (web scraping) para comparar los precios propios con los de la
competencia.

## Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión
de inventario de libros. Debido a la fluctuación en los costos de importación
de material bibliográfico, el sistema gestiona precios en diferentes monedas y
sigue de cerca la cotización del dólar.

En el Sprint 1 se desarrolló una aplicación de consola (CLI) en Python, con
persistencia en archivos CSV, que permite gestionar el inventario y cotizar
los libros según el valor del dólar. En el Sprint 2 la aplicación pasó a
persistir en una base de datos relacional (PostgreSQL en Supabase) con
SQLAlchemy, se migraron los datos a tablas y se incorporó la API de
cotizaciones del dólar.

En el Sprint 3 se descargan y obtienen datos de la web para trabajar con
ellos: la idea es conocer los precios de los competidores (librerías con venta
online, tomando como referencia el sitio Cúspide) para compararse con ellos y
competir de forma más informada. Se parte del último push de la entrega 2.

- Los datos iniciales se cargan desde los archivos `.sql` de migración.
- Un scraper hecho con Scrapy (`CuspideSpider`, con loaders y pipelines)
  busca cada libro del catálogo por título en Cúspide y obtiene, de los 10
  primeros resultados, el precio, la URL de la imagen, las formas de pago con
  su precio y la descripción detallada.
- Cada ejecución del scraper compara el precio interno con el precio web y
  genera un archivo CSV de alertas, según la diferencia de precio que ingresa
  el usuario antes de ejecutarlo.
- Se genera un reporte en Excel con el libro, el precio interno, el precio
  web, la diferencia y la fecha de extracción.
- Todas las operaciones del sistema quedan registradas en una tabla de
  auditoría mediante un decorador.
- La consola suma las opciones para ejecutar el scraping, generar el reporte
  y ver el historial de auditoría.

### Entidades

- **Libro**: cada título del catálogo (ISBN, título, autor, editorial, género, etc.).
- **Genero**: categoría literaria a la que pertenece un libro.
- **Editorial**: proveedor/distribuidora que provee los libros.
- **Moneda**: monedas en las que se expresa un precio (ARS, USD, etc.).
- **TipoCotizacion**: tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- **Precio**: valor monetario de un libro en una moneda determinada.
- **Stock**: cantidad disponible de cada libro.
- **CotizacionDolar**: registro histórico de cotizaciones por tipo y fecha.
- **PrecioWeb**: precio y datos de un libro obtenidos de la web de la competencia.
- **Auditoria**: registro de cada operación del sistema (acción, fecha y detalles).

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
│       ├── scraper/
│       │   ├── scrapy.cfg
│       │   ├── ejecutar.py
│       │   └── cuspide/ (items, loaders, pipelines, settings y spiders)
│       ├── services/services.py
│       ├── migrations/
│       │   ├── csv/
│       │   ├── sql/
│       │   └── migrations.py
│       ├── reportes/ (alertas CSV y reportes Excel generados)
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
