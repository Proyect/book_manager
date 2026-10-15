#@title Escritura de preload_data.py
"""Carga inicial de datos en la base desde los CSV de migrations/csv.

Recrea el esquema, genera los archivos .sql de migración, los ejecuta y
valida cada registro leyéndolo con las entidades del sistema. La ejecución
y la validación forman una única transacción: si algún registro no pasa las
validaciones de las entidades, la base queda sin datos migrados.
"""

from pathlib import Path
from typing import Dict, List

from sqlalchemy.sql import text

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    ejecutar_migraciones, migrar_datos)
from book_manager.models.models import EsquemaDB
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar, RepositorioEditorial, RepositorioGenero,
    RepositorioLibro, RepositorioMoneda, RepositorioPrecio, RepositorioStock,
    RepositorioTipoCotizacion)

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
    ]
    for repositorio in repositorios:
        repositorio.leer_todos()


def importar_datos(conexion_db: ConexionDB,
                   carpeta_csv: Path = DIRECTORIO_CSV,
                   carpeta_sql: Path = DIRECTORIO_SQL) -> Dict[str, int]:
    """Recrea la base y la puebla con los datos de migración.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.
        carpeta_csv (Path): Carpeta con los CSV de migración.
        carpeta_sql (Path): Carpeta donde se generan los archivos .sql.

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
    migrar_datos(str(carpeta_csv), str(carpeta_sql))
    with conexion_db.transaccion():
        resumen: Dict[str, int] = ejecutar_migraciones(
            conexion_db, str(carpeta_sql)
        )
        _validar_con_entidades(conexion_db)
    return resumen


def hay_datos(conexion_db: ConexionDB) -> bool:
    """Indica si la base tiene el esquema creado y libros cargados.

    Args:
        conexion_db (ConexionDB): Conexión a la base de datos.

    Returns:
        bool: True si existen todas las tablas y hay al menos un libro.
    """
    if not EsquemaDB(conexion_db).esta_creado():
        return False
    with conexion_db.transaccion() as conexion:
        cantidad: int = conexion.execute(
            text("SELECT COUNT(*) FROM libros")
        ).scalar()
    return cantidad > 0
