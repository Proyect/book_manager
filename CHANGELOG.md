# Changelog

Los cambios se registran del más reciente al más antiguo.

## Sprint 2

### [Ejercicio 8]

- Opción de menú **Obtener las cotizaciones por API**.
- Opción **Lista de precios bimonetaria**: precio de cada libro en pesos y en dólares según el tipo de dólar elegido.
- Opción **Exportar precios a CSV**: un archivo con el precio en pesos y en dólares para cada tipo de cotización (`data/exportaciones`).
- La consola informa los errores de base de datos sin interrumpir el programa.

### [Ejercicio 7]

- Archivo `.env` con `API_URL` de dolarapi.com, leído con python-dotenv.
- Servicio `ServicioCotizacionDolar` con la función `obtener_cotizaciones` que busca, descarga y registra (o actualiza) las cotizaciones en la base.
- Si la API informa un tipo de dólar que no existe, se crea automáticamente.
- Se usa la fecha de actualización informada por la API.

### [Ejercicio 6]

- Repositorio genérico `RepositorioDB` con CRUD completo sobre la base usando el context manager de transacciones.
- Repositorios de cada entidad reescritos para leer y escribir en las tablas, convirtiendo entre modelos ORM y entidades del dominio.
- Búsquedas con consultas SQLAlchemy: moneda por código, tipo por nombre, libro por ISBN, precios por libro, histórico de cotizaciones.
- `main.py` crea la conexión, las tablas y la carga inicial si la base está vacía.
- Los servicios dependen de `RepositorioDB` en lugar de `RepositorioCSV`.

### [Ejercicio 5]

- Función `migrar_datos(carpeta_csvs, carpeta_sqls)` en `migrations/migrations.py` que lee los CSV del TP1, convierte cada valor al tipo de su columna y puebla la base en una única transacción.
- Generación de los scripts `.sql` en `migrations/sql`: esquema (`00_esquema.sql`) y una sentencia INSERT por registro para cada tabla.
- `preload_data` reutiliza la migración para la carga inicial y verifica si la base ya tiene datos.

### [Ejercicio 4]

- Modelos ORM (tablas) `generos`, `editoriales`, `monedas`, `tipos_cotizacion`, `libros`, `precios`, `stock` y `cotizaciones_dolar`.
- Tipos de datos, claves primarias, valores únicos (ISBN, CUIT, código de moneda, nombres) y restricciones CHECK.
- Relaciones con claves foráneas: libro con editorial y género; precio con libro y moneda; stock 1 a 1 con libro; cotización con su tipo.
- Borrado en cascada de precios y stock al eliminar un libro.

### [Ejercicio 3]

- Context manager `ConexionDB.transaccion()` que abre la sesión, hace commit al terminar, rollback ante errores y siempre cierra la sesión.

### [Ejercicio 2]

- Clase `Base` (DeclarativeBase) de la que heredan los modelos.
- Clase `ConexionDB` que crea el engine de SQLAlchemy con la URL del `.env` (`DATABASE_URL`) o SQLite local por defecto.
- Activación de claves foráneas en SQLite, prueba de conexión, creación y borrado de tablas.

### [Ejercicio 1]

- Creación de la rama `Sprint_2` a partir de `Sprint_1`.
- Nuevas carpetas `database`, `models` y `migrations/sql`.
- `requirements.txt` con SQLAlchemy y python-dotenv.
- README actualizado al Sprint 2 (objetivo, introducción y contexto).

## Sprint 1

### [Punto 7]

- `main.py` arma repositorios y servicios e inicia la consola.
- Parámetro `import_default_data` para reimportar los datos de `migrations/csv` (se importan igual si no hay datos).
- `.gitignore` para excluir la carpeta de datos de trabajo y los `__pycache__`.

### [Punto 6]

- Interfaz de consola con menú principal y submenús por entidad.
- Listado, alta, modificación y baja de cada entidad (Enter conserva el valor actual al modificar).
- Operaciones de stock (ingreso y venta) y actualización en línea de cotizaciones.
- Menú de reportes: inventario valorizado, reposición, histórico de cotizaciones y comparación con Cúspide.

### [Punto 5]

- Archivos de migración en `migrations/csv` con al menos 10 registros por entidad.
- Función `importar_datos` que valida cada registro con las entidades y lo copia a los datos de trabajo.
- Función `hay_datos` para saber si el sistema ya tiene datos cargados.

### [Ejercicio 4]

- Servicio genérico `ServicioCRUD` con alta, lectura, modificación y baja validadas.
- Reglas de negocio: nombres, CUIT, códigos e ISBN únicos; no se borran registros con dependencias.
- Baja de libros en cascada (precios y stock) y alta de stock en cero al crear un libro.
- `ServicioStock` con ingreso de mercadería, ventas y libros para reponer.
- `ServicioCotizacion` con histórico, última cotización y actualización en línea desde dolarapi.com.
- `ServicioCompetencia` que busca el precio de cada libro en Cúspide (requests + BeautifulSoup).
- `ServicioReportes`: inventario valorizado en pesos, reposición y comparación con la competencia.

### [Ejercicio 3]

- Interfaces `IRepositorio`, `IRepositorioStock` e `IRepositorioCotizacionDolar` tomadas de la plantilla.
- Clase `ArchivoCSV` para leer y escribir los datos en archivos CSV (carpeta `data`).
- Repositorio genérico `RepositorioCSV` con CRUD completo e IDs autoincrementales.
- Repositorios de `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro` y `Precio`, resolviendo las relaciones por ID.
- Repositorios de `Stock` (clave: libro) y `CotizacionDolar` (clave: tipo y fecha).
- Búsquedas auxiliares: moneda por código, tipo por nombre, libro por ISBN y precios por libro.

### [Ejercicio 2]

- Creación de la clase abstracta `EntidadBase` con el `id` común a las entidades.
- Definición de las entidades `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`, `Precio`, `Stock` y `CotizacionDolar`.
- Encapsulamiento de los atributos con propiedades y validaciones (CUIT con dígito verificador, condición de IVA, ISBN, fecha y número de impresión, importes y cantidades).
- Relaciones entre objetos: `Libro` con `Editorial` y `Genero`; `Precio` y `Stock` con `Libro`; `CotizacionDolar` con `TipoCotizacion`.
- Método `to_dict()` en cada entidad para su posterior persistencia.

### [Ejercicio 1]

- Inicialización del repositorio y creación de la rama `Sprint_1`.
- Creación de la estructura de directorios del proyecto (`src/book_manager` con `entities`, `preload_data`, `repositories`, `services`, `migrations/csv` y `ui`).
- Creación de los archivos `README.md`, `CHANGELOG.md` y `requirements.txt`.
