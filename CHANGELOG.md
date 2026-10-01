# Changelog

Los cambios se registran del más reciente al más antiguo.

## [Ejercicio 3]

- Interfaces `IRepositorio`, `IRepositorioStock` e `IRepositorioCotizacionDolar` tomadas de la plantilla.
- Clase `ArchivoCSV` para leer y escribir los datos en archivos CSV (carpeta `data`).
- Repositorio genérico `RepositorioCSV` con CRUD completo e IDs autoincrementales.
- Repositorios de `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro` y `Precio`, resolviendo las relaciones por ID.
- Repositorios de `Stock` (clave: libro) y `CotizacionDolar` (clave: tipo y fecha).
- Búsquedas auxiliares: moneda por código, tipo por nombre, libro por ISBN y precios por libro.

## [Ejercicio 2]

- Creación de la clase abstracta `EntidadBase` con el `id` común a las entidades.
- Definición de las entidades `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`, `Precio`, `Stock` y `CotizacionDolar`.
- Encapsulamiento de los atributos con propiedades y validaciones (CUIT con dígito verificador, condición de IVA, ISBN, fecha y número de impresión, importes y cantidades).
- Relaciones entre objetos: `Libro` con `Editorial` y `Genero`; `Precio` y `Stock` con `Libro`; `CotizacionDolar` con `TipoCotizacion`.
- Método `to_dict()` en cada entidad para su posterior persistencia.

## [Ejercicio 1]

- Inicialización del repositorio y creación de la rama `Sprint_1`.
- Creación de la estructura de directorios del proyecto (`src/book_manager` con `entities`, `preload_data`, `repositories`, `services`, `migrations/csv` y `ui`).
- Creación de los archivos `README.md`, `CHANGELOG.md` y `requirements.txt`.
