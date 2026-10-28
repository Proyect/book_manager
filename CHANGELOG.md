# Changelog

Los cambios se registran del más reciente al más antiguo.

## Sprint 3

[Ejercicio 05]
- `ServicioReportes.generar_reporte_excel(tipo)`: reporte en Excel (openpyxl) en `reportes/reporte_precios_AAAAMMDD_HHMMSS.xlsx` con una fila por libro y los campos Libro, Precio interno, Precio web, Diferencia y Fecha de extracción.
- Formato del reporte: encabezado destacado, importes en pesos, fecha y hora de extracción, anchos de columna, fila de encabezado fija y filtros.
- Los libros que no se encontraron en la web quedan con el precio web, la diferencia y la fecha vacíos.

[Ejercicio 04]
- `ServicioReportes.ejecutar_scraping(umbral_porcentaje, tipo)`: ejecuta el scraper, compara el precio interno con el precio web de cada libro y, en cada ejecución, genera en `reportes/` un archivo CSV de alertas (`alertas_precios_AAAAMMDD_HHMMSS.csv`) con los libros cuya diferencia, en valor absoluto, es igual o mayor que la ingresada por el usuario.
- El CSV de alertas informa ISBN, libro, precio interno, precio web, diferencia en pesos y en %, umbral usado, tipo de alerta (precio interno mayor o menor al web), URL y fecha de extracción.
- `ComparacionPrecio` con el `PrecioWeb` elegido, la diferencia en pesos, la fecha de extracción y `supera_umbral`; nueva clase `ResultadoScraping`.
- `comparar_con_competencia` usa los precios obtenidos por el scraper (última extracción de cada libro); se elimina `ServicioCompetencia` (requests + BeautifulSoup) y BeautifulSoup de `requirements.txt`.

[Ejercicio 03]
- Proyecto Scrapy en `scraper/` (`scrapy.cfg` y paquete `cuspide` con `items`, `loaders`, `pipelines`, `settings` y `spiders`).
- Araña `CuspideSpider`: busca cada libro del catálogo por título en cuspide.com, toma solo los 10 primeros resultados de cada búsqueda y de la página de cada producto obtiene el precio, la URL de la imagen, las formas de pago con su precio y la descripción detallada (además del título, autor, ISBN y precio en dólares).
- `LibroWebItem` y `LibroWebLoader` (ItemLoader con procesadores de entrada y salida: limpieza de textos, conversión de importes con formato argentino, ISBN y unión de formas de pago y descripción).
- Pipelines: `ValidacionPipeline` (descarta resultados sin datos obligatorios), `DuplicadosPipeline` (descarta productos repetidos) y `ExportacionPipeline` (escribe los resultados en JSON Lines).
- Módulo `scraper/ejecutar.py`: ejecuta la araña con `CrawlerProcess` en un proceso propio (el reactor de Twisted solo puede iniciarse una vez por proceso), con respeto del robots.txt y demora entre consultas.
- Entidad `PrecioWeb`, tabla `precios_web` (borrado en cascada con el libro) y `RepositorioPrecioWeb` (resultados por libro y última extracción de cada libro).
- `ServicioScraping`: ejecuta la araña, guarda los resultados en la base en una sola transacción y elige el resultado que corresponde a cada libro (mismo ISBN o mismo título).
- `models.py` reorganizado en una clase por tabla (`GeneroModel`, `EditorialModel`, `MonedaModel`, `TipoCotizacionModel`, `LibroModel`, `PrecioModel`, `StockModel`, `CotizacionDolarModel` y `PrecioWebModel`); `EsquemaDB` crea las tablas a partir de los modelos.
- `main` crea las tablas nuevas en una base existente sin perder sus datos; `hay_datos` verifica la tabla de libros.

[Ejercicio 02]
- Función `cargar_datos_desde_sql(conexion_db, ruta_sql)` en `preload_data.py`: carga en la base los datos de un archivo `.sql` o de todos los archivos de migración de una carpeta (en orden de dependencias), en una sola transacción, y ajusta las secuencias de ids en PostgreSQL.
- `importar_datos` recrea el esquema y carga los datos desde los `.sql` de `migrations/sql`; los regenera desde los CSV solo si se pide (`regenerar_sql=True`) o si no existen.
- `migrations.py`: funciones públicas `ejecutar_archivo_sql` y `ajustar_secuencias`; se elimina `ejecutar_migraciones`, reemplazada por `cargar_datos_desde_sql` (sin código duplicado).

[Ejercicio 01]
- Creación de la rama `Sprint_3` a partir de `Sprint_2`.
- Nuevas carpetas `scraper` (proyecto Scrapy) y `reportes` (alertas CSV y reportes Excel generados, excluidos del repositorio en `.gitignore`).
- `requirements.txt` con Scrapy (scraper) y openpyxl (reportes Excel).
- README actualizado al Sprint 3 (objetivo, introducción y contexto, entidades y estructura).

## Sprint 2

[Ejercicio 08]
- Opción "Obtener cotizaciones por API" en el menú de cotizaciones del dólar:
  llama a `obtener_cotizaciones()` y muestra las cotizaciones registradas.
- Opción "Lista de precios bimonetaria" en el menú de reportes: precio de
  cada libro en pesos y en la moneda seleccionada, con el tipo de cotización
  elegido para convertir dólares.
- Opción "Exportar precios a CSV" en el menú de reportes: un archivo con una
  fila por libro y una columna por cada moneda registrada (por defecto en
  `data/exports/precios.csv`, ruta configurable).
- `ServicioReportes.precio_en_moneda`: usa el precio registrado en la moneda
  o, para USD, convierte el precio en pesos con la última cotización; sin
  dato para monedas sin cotización.
- `ServicioReportes.lista_bimonetaria` y `exportar_precios_csv` (módulo
  `csv`), y `ServicioPrecio.precio_vigente_en`.
- Consola con `ServicioCotizacionDolar`; se eliminan los alias temporales del
  Ejercicio 07; función `formatear_importe` y captura de `OSError` en el menú.
- Celda de prueba con entrada simulada: lista en USD y en EUR, exportación y
  lectura del CSV, cotizaciones por API y verificación de los alias.

[Ejercicio 07]
- Función `cargar_url_api()` en `services.py`: lee `API_URL` del archivo
  `.env` de la raíz del repositorio con `python-dotenv` (`dotenv_values`) y
  valida que exista; se elimina la URL fija del Sprint 1.
- `ServicioCotizacion` renombrado a `ServicioCotizacionDolar`, con la URL de
  la API y la conexión recibidas por constructor (URL validada y de solo
  lectura).
- Función `obtener_cotizaciones()`: descarga las cotizaciones de la API
  (`ConnectionError` ante fallas de red o formato) y las registra en la base,
  creando o actualizando por tipo y fecha.
- Fecha de cada cotización tomada de `fechaActualizacion` de la API; casas sin
  tipo asociado ignoradas; registro del lote completo en una transacción (un
  dato inválido no deja nada registrado).
- Alias temporales `ServicioCotizacion` y `actualizar_desde_api` para que la
  consola siga funcionando hasta el Ejercicio 08.
- `main.py` lee la URL del `.env` y se la pasa al servicio; `crear_servicios`
  acepta una URL opcional para las pruebas.
- Instalación de `python-dotenv` en la celda de imports del notebook.
- Celda de prueba: lectura del `.env`, registro con datos de ejemplo,
  actualización sin duplicados, rechazo atómico, API real y errores de red.

[Ejercicio 06]
- Todo el sistema persiste en PostgreSQL (Supabase): `ConexionDB()` sin URL
  arma la conexión con `SQLALCHEMY_DATABASE_URL` y `SUPABASE_DB_PASSWORD` del
  `.env` (contraseña insertada con `make_url`); sin credenciales usa una base
  SQLite local.
- La contraseña nunca se muestra: `url` y `repr` la ocultan, y los errores de
  URL no la incluyen; `pool_pre_ping` para las conexiones del pooler.
- Repositorios reescritos para persistir en la base de datos con SQL
  parametrizado: `RepositorioBaseSQL` (ejecución y conversión de errores de
  integridad en `ValueError`) y `RepositorioSQL[T]`, genérico con CRUD
  completo, que reemplaza a `ArchivoCSV` y `RepositorioCSV`.
- Interfaces de la cátedra sin cambios; los repositorios conservan sus
  nombres y sus búsquedas auxiliares (`leer_por_codigo`, `leer_por_nombre`
  con `lower()`, `leer_por_isbn`, `leer_por_libro`).
- Ids asignados por la base con `INSERT ... RETURNING id` (válido en
  PostgreSQL y SQLite) en lugar de `max(id) + 1`; sin caché en memoria.
- Transacciones compartidas en `ConexionDB`: una transacción abierta
  mientras otra está en curso se suma a la externa.
- `ServicioLibro` hace el alta (libro y stock) y la baja en cascada (precios,
  stock y libro) en una única transacción.
- `preload_data.py`: `importar_datos(conexion_db)` recrea el esquema, genera
  y ejecuta los `.sql` y valida cada registro con las entidades en la misma
  transacción; `hay_datos(conexion_db)` revisa el esquema y los libros.
- `main.py`: una `ConexionDB` compartida por todos los repositorios; con
  `import_default_data=False` usa la base existente o la carga si está vacía;
  parámetro opcional `conexion_db` para las pruebas.
- Celdas de prueba sobre bases SQLite temporales en `/tmp` (transacciones
  compartidas, repositorios y prueba integral) y prueba del sistema sobre
  Supabase (carga, alta y baja con secuencias ajustadas, restricciones y
  reporte).

[Ejercicio 05]
- Migración de datos en `migrations/migrations.py`, con la configuración de
  cada tabla en la clase `TablaMigracion` (columnas esperadas y columnas
  numéricas).
- `migrar_datos(carpeta_csvs, carpeta_sqls)`, con la firma del código base de
  la cátedra: lee los CSV del Sprint 1 y genera un `.sql` por tabla en
  `migrations/sql`, en orden de dependencias (`01_generos.sql` a
  `08_cotizaciones_dolar.sql`).
- Validación previa de todos los CSV (columnas exactas y valores numéricos):
  si uno es inválido no se escribe ningún archivo.
- Textos escapados con comillas simples duplicadas; archivos deterministas,
  sin fecha de generación.
- `ejecutar_migraciones(conexion_db, carpeta_sqls)`: puebla la base ejecutando
  los `.sql` con `text()` en una sola transacción (los `:` de los datos se
  escapan) y devuelve los registros insertados por tabla.
- En PostgreSQL, ajuste de los contadores de ids (`setval`) después de
  migrar, para que las altas nuevas no repitan ids de los CSV.
- Archivos `.sql` generados a partir de los CSV (108 registros en total).
- Celda de prueba sobre una base temporal en `/tmp`: conteos por tabla,
  relaciones con `JOIN`, determinismo, rollback al migrar dos veces y errores
  de entrada.

[Ejercicio 04]
- Esquema relacional en `models/models.py`, escrito en SQL y ejecutado con
  `text()` (sin modelos declarativos, como indica el material de la cátedra).
- 8 tablas: `generos`, `editoriales`, `monedas`, `tipos_cotizacion`,
  `libros`, `precios`, `stock` y `cotizaciones_dolar`, con tipos de datos,
  claves primarias (simple, 1:1 en `stock` y compuesta en
  `cotizaciones_dolar`) y 6 claves foráneas.
- Sentencias adaptadas al motor: ids `GENERATED BY DEFAULT AS IDENTITY` en
  PostgreSQL y `INTEGER PRIMARY KEY` en SQLite; tablas existentes consultadas
  en el catálogo de cada motor.
- Restricciones `UNIQUE` (CUIT, código de moneda, ISBN y precio por libro,
  moneda y fecha), índices únicos sobre `lower(nombre)` para géneros y tipos
  de cotización, y `CHECK` (largos, rangos, condición de IVA e importes).
- Integridad referencial sin borrado en cascada: la base impide borrar
  registros en uso y las bajas en cascada siguen en los servicios.
- Clase `EsquemaDB` con `crear_tablas()`, `eliminar_tablas()`,
  `tablas_existentes()` y `esta_creado()`, en orden de dependencias e
  idempotentes (`IF NOT EXISTS`).
- Celda de prueba sobre una base temporal en `/tmp`: creación, estructura,
  claves foráneas, id autoincremental, restricciones y eliminación.

[Ejercicio 03]
- Context manager `Transaccion` en `database/connection.py`, implementado como
  clase con `__enter__` y `__exit__`.
- Al entrar abre una conexión con `conectar()` e inicia la transacción; al
  salir confirma (`commit`) si el bloque terminó bien o deshace (`rollback`)
  si hubo una excepción, y siempre cierra la conexión.
- Las excepciones se propagan a quien usa el bloque `with`.
- Método `ConexionDB.transaccion()` que crea un context manager nuevo, de un
  solo uso, por cada operación.
- Celda de prueba sobre una base temporal en `/tmp`: commit, rollback con
  propagación del error, atomicidad ante una violación de clave foránea y
  usos inválidos.

[Ejercicio 02]
- Clase `ConexionDB` en `database/connection.py`, única responsable de crear
  el engine de SQLAlchemy y entregar conexiones.
- Base SQLite por defecto en `src/book_manager/data/book_manager.db` (excluida
  del repositorio), con URL configurable por constructor.
- Engine privado: las conexiones solo se obtienen con `conectar()`, que activa
  las claves foráneas (`PRAGMA foreign_keys = ON`) y deja la conexión sin
  transacción abierta.
- Creación automática de la carpeta del archivo SQLite si no existe.
- Validación de la URL y del parámetro `echo`; `cerrar()` libera el engine.
- Celda de prueba sobre una base temporal en `/tmp`: transacciones,
  integridad referencial, validaciones y cierre.

[Ejercicio 01]
- Creación de la rama `Sprint_2` a partir de la rama `Sprint_1`.
- Nuevas carpetas `database`, `models` y `migrations/sql`, con los módulos
  `connection.py`, `models.py` y `migrations.py`.
- Archivo `.env` con la URL de la API de cotizaciones (`API_URL`) y la
  conexión a Supabase (`SQLALCHEMY_DATABASE_URL` y `SUPABASE_DB_PASSWORD`),
  versionado por indicación de la cátedra; la contraseña se toma del secret
  de Colab o del `.env` existente y nunca se escribe en el notebook.
- `requirements.txt` con `SQLAlchemy`, `python-dotenv` y `psycopg[binary]`.
- `.gitignore` excluye las bases de datos SQLite (`*.db`).
- README actualizado al Sprint 2 (objetivo, introducción, contexto y estructura).
- Encabezados del CHANGELOG del Sprint 1 normalizados al formato `[Ejercicio XX]`.

## Sprint 1

[Ejercicio 07]
- `main.py` arma repositorios y servicios e inicia la consola.
- Parámetro `import_default_data` para reimportar los datos de `migrations/csv` (se importan igual si no hay datos).
- `.gitignore` para excluir la carpeta de datos de trabajo y los `__pycache__`.

[Ejercicio 06]
- Interfaz de consola con menú principal y submenús por entidad.
- Listado, alta, modificación y baja de cada entidad (Enter conserva el valor actual al modificar).
- Operaciones de stock (ingreso y venta) y actualización en línea de cotizaciones.
- Menú de reportes: inventario valorizado, reposición, histórico de cotizaciones y comparación con Cúspide.

[Ejercicio 05]
- Archivos de migración en `migrations/csv` con al menos 10 registros por entidad.
- Función `importar_datos` que valida cada registro con las entidades y lo copia a los datos de trabajo.
- Función `hay_datos` para saber si el sistema ya tiene datos cargados.

[Ejercicio 04]
- Servicio genérico `ServicioCRUD` con alta, lectura, modificación y baja validadas.
- Reglas de negocio: nombres, CUIT, códigos e ISBN únicos; no se borran registros con dependencias.
- Baja de libros en cascada (precios y stock) y alta de stock en cero al crear un libro.
- `ServicioStock` con ingreso de mercadería, ventas y libros para reponer.
- `ServicioCotizacion` con histórico, última cotización y actualización en línea desde dolarapi.com.
- `ServicioCompetencia` que busca el precio de cada libro en Cúspide (requests + BeautifulSoup).
- `ServicioReportes`: inventario valorizado en pesos, reposición y comparación con la competencia.

[Ejercicio 03]
- Interfaces `IRepositorio`, `IRepositorioStock` e `IRepositorioCotizacionDolar` tomadas de la plantilla.
- Clase `ArchivoCSV` para leer y escribir los datos en archivos CSV (carpeta `data`).
- Repositorio genérico `RepositorioCSV` con CRUD completo e IDs autoincrementales.
- Repositorios de `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro` y `Precio`, resolviendo las relaciones por ID.
- Repositorios de `Stock` (clave: libro) y `CotizacionDolar` (clave: tipo y fecha).
- Búsquedas auxiliares: moneda por código, tipo por nombre, libro por ISBN y precios por libro.

[Ejercicio 02]
- Creación de la clase abstracta `EntidadBase` con el `id` común a las entidades.
- Definición de las entidades `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`, `Precio`, `Stock` y `CotizacionDolar`.
- Encapsulamiento de los atributos con propiedades y validaciones (CUIT con dígito verificador, condición de IVA, ISBN, fecha y número de impresión, importes y cantidades).
- Relaciones entre objetos: `Libro` con `Editorial` y `Genero`; `Precio` y `Stock` con `Libro`; `CotizacionDolar` con `TipoCotizacion`.
- Método `to_dict()` en cada entidad para su posterior persistencia.

[Ejercicio 01]
- Inicialización del repositorio y creación de la rama `Sprint_1`.
- Creación de la estructura de directorios del proyecto (`src/book_manager` con `entities`, `preload_data`, `repositories`, `services`, `migrations/csv` y `ui`).
- Creación de los archivos `README.md`, `CHANGELOG.md` y `requirements.txt`.
