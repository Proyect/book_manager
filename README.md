# Book Manager

**Trabajo Práctico Integrador** — Seminario de Actualización I (Lic. en Ciencia de Datos, UGR) — Grupo 39

## Sprint actual

**Sprint 2**

## Objetivo

Consolidar las bases del manejo de bases de datos relacionales: normalización, conexión segura, carga inicial de datos y consultas a APIs externas, aplicando programación orientada a objetos con el ORM SQLAlchemy.

## Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

En el Sprint 1 se desarrolló una aplicación de consola (CLI) en Python que persistía los datos en archivos CSV. En este Sprint 2 se amplía el alcance:

- La aplicación persiste en una **base de datos relacional** (SQLite por defecto) usando el ORM **SQLAlchemy**.
- Se **migran** todos los datos cargados en los archivos CSV del Sprint 1 a tablas relacionales, generando los scripts `.sql` de la migración.
- La URL de la API de cotizaciones se configura en un archivo **`.env`** (python-dotenv) y las cotizaciones obtenidas se registran en la base.
- Se agregan al menú la obtención de cotizaciones por API, la lista de precios **bimonetaria** y la **exportación de precios a CSV**.

### Entidades / tablas

| Entidad | Tabla | Relaciones |
|---|---|---|
| Genero | `generos` | 1 a N con libros |
| Editorial | `editoriales` | 1 a N con libros |
| Moneda | `monedas` | 1 a N con precios |
| TipoCotizacion | `tipos_cotizacion` | 1 a N con cotizaciones |
| Libro | `libros` | N a 1 con editorial y género |
| Precio | `precios` | N a 1 con libro y moneda |
| Stock | `stock` | 1 a 1 con libro |
| CotizacionDolar | `cotizaciones_dolar` | N a 1 con tipo (clave: tipo y fecha) |

## Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/connection.py      # ConexionDB y context manager de transacciones
│       ├── entities/entities.py        # Entidades del dominio
│       ├── models/models.py            # Tablas (modelos ORM)
│       ├── preload_data/preload_data.py
│       ├── repositories/repositories.py
│       ├── services/services.py
│       ├── migrations/
│       │   ├── csv/                    # Datos del Sprint 1
│       │   ├── sql/                    # Scripts generados por la migración
│       │   └── migrations.py
│       ├── ui/console.py
│       └── main.py
├── .env
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## Configuración (`.env`)

```
API_URL=https://dolarapi.com/v1/dolares
# DATABASE_URL=sqlite:///ruta/a/book_manager.db  (opcional)
```

## Ejecución

```python
from book_manager.main import main
main(import_default_data=False)
```

## Integrantes

- Ariel Marcelo Diaz
- Marco Fouad Abboud
- Matias Gabriel Gallardo
- Nestor Fabian Leon
- Sebastian Luna
