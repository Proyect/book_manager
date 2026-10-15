# Changelog

Los cambios se registran del más reciente al más antiguo.

## Sprint 2

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
- Archivo `.env` con la URL de la API de cotizaciones (`API_URL`), solo con
  configuración pública.
- `requirements.txt` con `SQLAlchemy` y `python-dotenv`.
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
