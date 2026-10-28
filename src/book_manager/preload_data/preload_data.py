#@title Escritura de preload_data.py
"""Carga inicial de datos en la base desde los archivos .sql de migración.

Recrea el esquema, carga los datos desde los archivos .sql de
migrations/sql (opcionalmente, regenerándolos antes desde los CSV de
migrations/csv) y valida cada registro leyéndolo con las entidades del
sistema. La carga y la validación forman una única transacción: si algún
registro no pasa las validaciones de las entidades, la base queda sin datos
migrados.
"""

from pathlib import Path
from typing import Dict, List

from sqlalchemy.sql import text

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    TABLAS_MIGRACION, ajustar_secuencias, ejecutar_archivo_sql, migrar_datos,
    nombre_archivo_sql)
from book_manager.models.models import EsquemaDB
from book_manager.repositories.repositories import (
    RepositorioAuditoria, RepositorioCotizacionDolar, RepositorioEditorial,
    RepositorioGenero, RepositorioLibro, RepositorioMoneda, RepositorioPrecio,
    RepositorioPrecioWeb, RepositorioStock, RepositorioTipoCotizacion)

DIRECTORIO_MIGRACIONES: Path = (
    Path(__file__).resolve().parent.parent / "migrations"
)
DIRECTORIO_CSV: Path = DIRECTORIO_MIGRACIONES / "csv"
DIRECTORIO_SQL: Path = DIRECTORIO_MIGRACIONES / "sql"


def _validar_con_entidades(conexion_db: ConexionDB) -> None:
    """Lee todos los registros con los repositorios para validarlos.

    Cada repositorio construye sus entidades al leer, y las entidades
    validan sus datos en los setters.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.

    Raises:
        ValueError: Si algún registro no es válido para su entidad.
        TypeError: Si algún registro tiene un tipo de dato inválido.
    """
    repo_genero = RepositorioGenero(conexion_db)
    repo_editorial = RepositorioEditorial(conexion_db)
    repo_moneda = RepositorioMoneda(conexion_db)
    repo_tipo = RepositorioTipoCotizacion(conexion_db)
    repo_libro = RepositorioLibro(conexion_db, repo_editorial, repo_genero)
    repositorios: List[object] = [
        repo_genero, repo_editorial, repo_moneda, repo_tipo, repo_libro,
        RepositorioPrecio(conexion_db, repo_libro, repo_moneda),
        RepositorioStock(conexion_db, repo_libro),
        RepositorioCotizacionDolar(conexion_db, repo_tipo),
        RepositorioPrecioWeb(conexion_db, repo_libro),
        RepositorioAuditoria(conexion_db),
    ]
    for repositorio in repositorios:
        repositorio.leer_todos()


def _tabla_de_archivo(ruta: Path) -> str:
    """Nombre de la tabla de un archivo .sql de migración.

    Args:
        ruta (Path): Archivo con el formato NN_tabla.sql (ej. 05_libros.sql).

    Returns:
        str: Nombre de la tabla (ej. 'libros').
    """
    prefijo, _, resto = ruta.stem.partition("_")
    return resto if prefijo.isdigit() and resto else ruta.stem


def cargar_datos_desde_sql(conexion_db: ConexionDB,
                           ruta_sql: Path = DIRECTORIO_SQL) -> Dict[str, int]:
    """Carga en la base los datos de uno o varios archivos .sql.

    Si la ruta es una carpeta, se ejecutan los archivos de migración en el
    orden de dependencias de las tablas (los que existan); si es un archivo,
    solo ese. Todo se ejecuta en una sola transacción: si una sentencia
    falla, no queda nada cargado. Las tablas deben existir.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.
        ruta_sql (Path): Archivo .sql o carpeta con los archivos .sql (por
            defecto, migrations/sql).

    Returns:
        Dict[str, int]: Cantidad de registros cargados por tabla.

    Raises:
        TypeError: Si conexion_db no es una ConexionDB.
        FileNotFoundError: Si la ruta no existe o la carpeta no tiene
            archivos .sql de migración.
    """
    if not isinstance(conexion_db, ConexionDB):
        raise TypeError("La carga requiere una ConexionDB.")
    ruta: Path = Path(ruta_sql)
    if ruta.is_dir():
        archivos: List[Path] = [
            ruta / nombre_archivo_sql(posicion, config.tabla)
            for posicion, config in enumerate(TABLAS_MIGRACION, start=1)
            if (ruta / nombre_archivo_sql(posicion, config.tabla)).is_file()
        ]
        if not archivos:
            raise FileNotFoundError(
                f"La carpeta {ruta} no tiene archivos .sql de migración."
            )
    elif ruta.is_file():
        archivos = [ruta]
    else:
        raise FileNotFoundError(f"No existe {ruta}.")

    resumen: Dict[str, int] = {}
    with conexion_db.transaccion() as conexion:
        for archivo in archivos:
            resumen[_tabla_de_archivo(archivo)] = ejecutar_archivo_sql(
                conexion, archivo
            )
        ajustar_secuencias(conexion)
    return resumen


def importar_datos(conexion_db: ConexionDB,
                   carpeta_csv: Path = DIRECTORIO_CSV,
                   carpeta_sql: Path = DIRECTORIO_SQL,
                   regenerar_sql: bool = False) -> Dict[str, int]:
    """Recrea la base y la puebla con los datos de los archivos .sql.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.
        carpeta_csv (Path): Carpeta con los CSV de migración.
        carpeta_sql (Path): Carpeta con los archivos .sql de migración.
        regenerar_sql (bool): Si es True, antes de cargar se vuelven a
            generar los archivos .sql desde los CSV.

    Returns:
        Dict[str, int]: Cantidad de registros importados por tabla.

    Raises:
        TypeError: Si conexion_db no es una ConexionDB.
        ValueError: Si algún CSV o registro no es válido.
    """
    if not isinstance(conexion_db, ConexionDB):
        raise TypeError("La importación requiere una ConexionDB.")
    esquema = EsquemaDB(conexion_db)
    esquema.eliminar_tablas()
    esquema.crear_tablas()
    if regenerar_sql or not any(Path(carpeta_sql).glob("*.sql")):
        migrar_datos(str(carpeta_csv), str(carpeta_sql))
    with conexion_db.transaccion():
        resumen: Dict[str, int] = cargar_datos_desde_sql(
            conexion_db, carpeta_sql
        )
        _validar_con_entidades(conexion_db)
    return resumen


def hay_datos(conexion_db: ConexionDB) -> bool:
    """Indica si la base tiene la tabla de libros con datos cargados.

    Las tablas nuevas de un sprint (que una base existente todavía no
    tiene) se crean con EsquemaDB.crear_tablas, sin perder los datos.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.

    Returns:
        bool: True si existe la tabla libros y tiene al menos un libro.
    """
    if "libros" not in EsquemaDB(conexion_db).tablas_existentes():
        return False
    with conexion_db.transaccion() as conexion:
        cantidad: int = conexion.execute(
            text("SELECT COUNT(*) FROM libros")
        ).scalar()
    return cantidad > 0
